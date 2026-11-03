"""Real POSIX atomic token registry operations and live HTTP auth revocation."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import base64

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import publisher_intake_service as gateway
import publisher_token_lifecycle as admin
import private_publisher_inbox as inbox


@unittest.skipUnless(os.name == "posix", "owner-private POSIX token file lifecycle")
class PublisherTokenLifecycleTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)
        self.quarantine = inbox.init_root(self.work / "quarantine")
        self.incoming = inbox.init_root(self.work / "incoming")
        self.registry_dir = inbox.init_root(self.work / "registry")
        self.registry = self.registry_dir / "tokens.json"
        self.old_token = gateway.provision(self.registry, "publisher-first")
        self.server = gateway.LocalIntakeServer(
            self.quarantine, self.incoming, self.registry)
        self.worker = threading.Thread(target=self.server.serve_forever,
                                       daemon=True)
        self.worker.start()
        self.addCleanup(self.stop)
        self.body = b"not-an-executable-publisher-credential-test"
        self.claim = {
            "release": {
                "app_id": "sample", "platform": "windows",
                "version": "1.0.1",
                "asset_url": ("https://github.com/rezamahrm100-ops/publisher-first/"
                              "releases/download/v1.0.1/test.exe"),
                "sha256": hashlib.sha256(self.body).hexdigest(),
                "size_bytes": len(self.body),
            },
            "source_repo": "publisher-first",
            "source_sha": "a" * 40,
            "package_id": None,
            "version_code": None,
        }

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.worker.join(timeout=5)

    def send(self, token, name="publisher-first"):
        encoded = base64.b64encode(json.dumps(self.claim).encode()).decode()
        req = Request("http://127.0.0.1:%d/v1/submissions" % self.server.server_port,
                      data=self.body, method="POST", headers={
                          "Authorization": "Bearer " + token,
                          "X-HamApp-Publisher": name,
                          "X-HamApp-Candidate-Base64": encoded,
                          "Content-Type": "application/octet-stream",
                      })
        try:
            with urlopen(req, timeout=5) as response:
                return response.status, json.load(response)
        except HTTPError as exc:
            return exc.code, json.load(exc)

    def test_rotate_becomes_immediately_effective_on_running_server(self):
        self.assertEqual(self.send(self.old_token)[0], 202)
        before = gateway.load_credentials(self.registry)["publisher-first"]
        change = admin.change_registry(self.registry, "rotate", "publisher-first")
        replacement = change["one_time_secret"]
        self.assertGreaterEqual(len(replacement), 64)
        self.assertNotEqual(replacement, self.old_token)
        self.assertNotEqual(gateway.load_credentials(self.registry)["publisher-first"], before)
        self.assertEqual(self.send(self.old_token)[0], 401)
        self.assertEqual(self.send(replacement)[0], 202)
        self.assertEqual(len(list(self.quarantine.iterdir())), 2)
        self.assertFalse(change["publisher_identity_independently_verified"])
        self.assertFalse(change["owner_publication_approved"])
        text = self.registry.read_text("utf-8")
        self.assertNotIn(replacement, text)
        self.assertNotIn(self.old_token, text)

    def test_revoke_only_publisher_leaves_valid_deny_all_registry(self):
        revoked = admin.change_registry(self.registry, "revoke", "publisher-first")
        self.assertIsNone(revoked["one_time_secret"])
        self.assertEqual(gateway.load_credentials(self.registry), {})
        self.assertEqual(self.send(self.old_token)[0], 401)
        self.assertEqual(len(list(self.quarantine.iterdir())), 0)

    def test_add_and_per_tenant_token_binding_with_live_server(self):
        created = admin.change_registry(self.registry, "add", "publisher-second")
        self.assertEqual(self.send(self.old_token, "publisher-second")[0], 401)
        self.assertEqual(self.send(created["one_time_secret"], "publisher-first")[0], 401)
        self.assertEqual(self.send(self.old_token, "publisher-first")[0], 202)
        self.assertEqual(len(gateway.load_credentials(self.registry)), 2)
        self.assertEqual((self.registry.stat().st_mode & 0o077), 0)

    def test_bad_state_fails_without_mutating_registry(self):
        original = self.registry.read_bytes()
        for action, name in (("add", "publisher-first"),
                             ("revoke", "nonexistent"),
                             ("rotate", "nonexistent"),
                             ("unknown", "publisher-first"),
                             ("add", "../traversal")):
            with self.subTest(action=action, name=name):
                with self.assertRaises(ValueError):
                    admin.change_registry(self.registry, action, name)
        self.assertEqual(self.registry.read_bytes(), original)

    def test_corrupt_or_insecure_registry_fails_closed_on_running_server(self):
        self.registry.chmod(0o644)
        self.assertEqual(self.send(self.old_token)[0], 503)
        self.registry.chmod(0o600)
        self.assertEqual(self.send(self.old_token)[0], 202)
        self.registry.write_text("{broken json", encoding="utf-8")
        self.assertEqual(self.send(self.old_token)[0], 503)
        self.assertEqual(len(list(self.quarantine.iterdir())), 1)

    def test_lock_file_and_credentials_private_and_no_public_checkout_changes(self):
        admin.change_registry(self.registry, "rotate", "publisher-first")
        lock = self.registry_dir / (self.registry.name + ".lock")
        self.assertTrue(lock.is_file())
        self.assertEqual(lock.stat().st_mode & 0o077, 0)
        self.assertEqual(self.registry.stat().st_mode & 0o077, 0)
        self.assertEqual(len(list(self.registry_dir.iterdir())), 2)


if __name__ == "__main__":
    unittest.main()
