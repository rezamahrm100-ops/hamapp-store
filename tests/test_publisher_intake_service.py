"""Real loopback HTTP/upload and private-file checks; synthetic EXE bytes only."""
import base64
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

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import private_publisher_inbox as inbox
import publisher_intake_service as gateway

@unittest.skipUnless(os.name == "posix", "private POSIX gateway only")
class PublisherGatewayTests(unittest.TestCase):
    def setUp(self):
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        self.home = Path(work.name)
        self.root = inbox.init_root(self.home / "inbox")
        self.temp = inbox.init_root(self.home / "incoming")
        self.credentials = self.home / "credential.json"
        self.token = gateway.provision(self.credentials, "sample-publisher")
        self.body = b"synthetic non-executable Windows fixture bytes"
        self.candidate = {
            "release": {
                "app_id": "sample",
                "platform": "windows",
                "version": "1.2.3",
                "asset_url": "https://github.com/rezamahrm100-ops/sample-publisher/releases/download/v1.2.3/candidate.exe",
                "sha256": hashlib.sha256(self.body).hexdigest(),
                "size_bytes": len(self.body)
            },
            "source_repo": "sample-publisher",
            "source_sha": "a" * 40,
            "package_id": None,
            "version_code": None
        }
        self.server = gateway.LocalIntakeServer(self.root, self.temp, self.credentials)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop_server)

    def stop_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def upload(self, *, token=None, publisher="sample-publisher", candidate=None, data=None,
               path="/v1/submissions", content_type="application/octet-stream"):
        encoded = base64.b64encode(json.dumps(
            candidate if candidate is not None else self.candidate,
            separators=(",", ":")).encode("utf-8")).decode("ascii")
        req = Request(
            "http://127.0.0.1:%s%s" % (self.server.server_port, path),
            data=self.body if data is None else data, method="POST",
            headers={
                "Authorization": "Bearer " + (self.token if token is None else token),
                "X-HamApp-Publisher": publisher,
                "X-HamApp-Candidate-Base64": encoded,
                "Content-Type": content_type,
            })
        try:
            with urlopen(req, timeout=5) as response:
                return response.status, json.load(response)
        except HTTPError as exc:
            return exc.code, json.load(exc)

    def test_real_private_transport_authentication_and_staging(self):
        status, result = self.upload()
        self.assertEqual(status, 202)
        self.assertEqual(result["status"], "quarantined")
        self.assertTrue(result["local_token_authenticated"])
        self.assertFalse(result["publisher_identity_independently_verified"])
        self.assertFalse(result["owner_review_approved"])
        self.assertFalse(result["public_distribution_authorized"])
        folder, record = inbox.load(self.root, result["submission_id"])
        self.assertEqual((folder / "candidate.exe").read_bytes(), self.body)
        self.assertEqual(record["claimed_publisher"], "sample-publisher")
        self.assertFalse(record["production_distribution_authorized"])
        self.assertEqual(list(self.temp.iterdir()), [])
        self.assertEqual(inbox.verify_events(folder)[0], "quarantined")

    def test_bad_token_and_cross_publisher_denied_without_private_write(self):
        self.assertEqual(self.upload(token="A" * 64)[0], 401)
        self.assertEqual(self.upload(publisher="other-publisher")[0], 401)
        self.assertEqual(list(self.root.iterdir()), [])
        self.assertEqual(list(self.temp.iterdir()), [])

    def test_authenticated_publisher_cannot_claim_another_source(self):
        candidate = json.loads(json.dumps(self.candidate))
        candidate["source_repo"] = "not-me"
        self.assertEqual(self.upload(candidate=candidate)[0], 422)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_actual_body_digest_mismatch_and_missing_bytes(self):
        self.assertEqual(self.upload(data=b"X" * len(self.body))[0], 422)
        self.assertEqual(self.upload(data=b"short")[0], 422)
        self.assertEqual(list(self.root.iterdir()), [])
        self.assertEqual(list(self.temp.iterdir()), [])

    def test_invalid_method_path_type_and_bad_candidate_denied(self):
        self.assertEqual(self.upload(path="/v1/approve")[0], 404)
        self.assertEqual(self.upload(content_type="text/plain")[0], 422)
        candidate = json.loads(json.dumps(self.candidate))
        candidate["release"]["asset_url"] = "http://evil.example/unsafe.exe"
        self.assertEqual(self.upload(candidate=candidate)[0], 422)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_enforces_private_tenant_quota_before_copy(self):
        self.assertEqual(self.upload()[0], 202)
        previous = gateway.MAX_SUBMISSIONS_PER_PUBLISHER
        try:
            gateway.MAX_SUBMISSIONS_PER_PUBLISHER = 1
            self.assertEqual(self.upload()[0], 422)
        finally:
            gateway.MAX_SUBMISSIONS_PER_PUBLISHER = previous
        self.assertEqual(len(list(self.root.iterdir())), 1)

    def test_credential_file_and_network_binding_are_fail_closed(self):
        with self.assertRaises(gateway.IntakeServiceError):
            gateway.LocalIntakeServer(self.root, self.temp, self.credentials, host="0.0.0.0")
        self.credentials.chmod(0o644)
        with self.assertRaises(gateway.IntakeServiceError):
            gateway.load_credentials(self.credentials)
        self.credentials.chmod(0o600)
        with self.assertRaises(gateway.IntakeServiceError):
            gateway.provision(self.credentials, "sample-publisher")
        self.assertEqual(len(self.token) >= 64, True)

    def test_credentials_have_no_plaintext_token_or_public_release_flags(self):
        raw = self.credentials.read_text(encoding="utf-8")
        self.assertNotIn(self.token, raw)
        self.assertEqual(gateway.load_credentials(self.credentials)["sample-publisher"],
                         hashlib.sha256(self.token.encode("ascii")).hexdigest())
        self.assertNotIn("approved", raw)
        self.assertNotIn("published", raw)

if __name__ == "__main__":
    unittest.main()
