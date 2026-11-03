"""Actual authenticated loopback streaming client -> quarantine integration tests."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import local_publisher_submit as client
import private_publisher_inbox as inbox
import publisher_intake_service as gateway

@unittest.skipUnless(os.name == "posix", "POSIX owner-local gateway only")
class LocalSubmitTests(unittest.TestCase):
    def setUp(self):
        base = tempfile.TemporaryDirectory()
        self.addCleanup(base.cleanup)
        self.base = Path(base.name)
        self.root = inbox.init_root(self.base / "quarantine")
        self.temp = inbox.init_root(self.base / "uploads")
        creds = self.base / "auth.json"
        token = gateway.provision(creds, "sample-publisher")
        self.tokenfile = self.base / "my-secret"
        self.tokenfile.write_text(token + "\n", encoding="ascii")
        self.tokenfile.chmod(0o600)
        self.artifact = self.base / "demo.exe"
        self.artifact.write_bytes(b"synthetic Windows application, non-executable bytes")
        self.candidate = self.base / "claim.json"
        manifest = {
            "app_id": "demo", "platform": "windows", "version": "1.2.3",
            "asset_url": "https://github.com/rezamahrm100-ops/sample-publisher/releases/download/v1.2.3/demo.exe",
            "sha256": hashlib.sha256(self.artifact.read_bytes()).hexdigest(),
            "size_bytes": self.artifact.stat().st_size
        }
        self.candidate.write_text(json.dumps({
            "source_repo": "sample-publisher", "source_sha": "a" * 40,
            "package_id": None, "version_code": None, "release": manifest
        }), encoding="utf-8")
        self.server = gateway.LocalIntakeServer(self.root, self.temp, creds)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop)

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def call(self):
        return client.submit(self.candidate, self.artifact, "sample-publisher",
                             self.tokenfile, port=self.server.server_port)

    def test_real_streaming_client_sends_exact_private_file_and_returns_no_approval(self):
        reply = self.call()
        self.assertTrue(reply["local_token_authenticated"])
        self.assertFalse(reply["owner_review_approved"])
        self.assertFalse(reply["public_distribution_authorized"])
        folder, receipt = inbox.load(self.root, reply["submission_id"])
        self.assertEqual((folder / "candidate.exe").read_bytes(), self.artifact.read_bytes())
        self.assertFalse(receipt["publisher_identity_authenticated"])
        self.assertEqual(list(self.temp.iterdir()), [])

    def test_modified_artifact_denied_before_network_side_effects(self):
        self.artifact.write_bytes(b"changed after manifest was pinned")
        with self.assertRaises(ValueError):
            self.call()
        self.assertEqual(list(self.root.iterdir()), [])

    def test_secret_must_be_private_and_not_in_cli_arguments(self):
        self.tokenfile.chmod(0o644)
        with self.assertRaises(ValueError):
            self.call()
        self.assertEqual(list(self.root.iterdir()), [])

    def test_cross_source_publisher_claim_not_accepted(self):
        data = json.loads(self.candidate.read_text())
        data["source_repo"] = "other-publisher"
        self.candidate.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            self.call()
        self.assertEqual(list(self.root.iterdir()), [])

if __name__ == "__main__":
    unittest.main()
