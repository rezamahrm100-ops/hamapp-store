"""Real private HTTPS publisher handshake and quarantine from Windows client adapter.

The service uses disposable local OpenSSL cert and a one-run publisher token.
No real credentials, paid services, release approval or owner Windows host.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import ssl
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from windows_client import publisher_connection as client
import private_publisher_inbox as inbox
import publisher_intake_service as gateway
import remote_publisher_tls_service as service


@unittest.skipUnless(os.name == "posix" and shutil.which("openssl"),
                     "real POSIX private TLS server and OpenSSL are required")
class OwnerPublisherLiveConnection(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="hamapp-owner-live-tls-")
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.quarantine = inbox.init_root(self.root / "quarantine")
        self.incoming = inbox.init_root(self.root / "incoming")
        self.credentials = self.root / "credentials.json"
        self.publisher = "owner-example"
        self.token = gateway.provision(self.credentials, self.publisher)
        self.cert = self.root / "server.pem"
        self.key = self.root / "server.key"
        created = subprocess.run([
            "openssl", "req", "-new", "-x509", "-newkey", "rsa:2048",
            "-noenc", "-days", "1", "-subj", "/CN=localhost",
            "-addext", "subjectAltName=DNS:localhost,IP:127.0.0.1",
            "-keyout", str(self.key), "-out", str(self.cert)
        ], capture_output=True, text=True, timeout=30)
        if created.returncode:
            raise AssertionError("ephemeral local TLS test certificate was not generated")
        self.key.chmod(0o600)
        self.server = service.TLSQuarantineServer(
            self.quarantine, self.incoming, self.credentials, self.cert, self.key)
        self.worker = threading.Thread(
            target=self.server.serve_forever,
            kwargs={"poll_interval": 0.1}, daemon=True)
        self.worker.start()
        self.addCleanup(self.shutdown)
        self.details = {
            "publisher": self.publisher,
            "origin": f"https://localhost:{self.server.server_port}",
            "trusted_ca": str(self.cert),
            "server_cert_sha256": hashlib.sha256(
                ssl.PEM_cert_to_DER_cert(self.cert.read_text("ascii"))).hexdigest()
        }
        self.body = b"NON-EXECUTABLE-E2E-PUBLISHER-CONNECTIVITY-FIXTURE"
        self.artifact = self.root / "program.exe"
        self.artifact.write_bytes(self.body)
        self.candidate = self.root / "candidate.json"
        self.candidate.write_text(json.dumps({
            "release": {
                "app_id": "sample",
                "platform": "windows",
                "version": "1.2.3",
                "asset_url": ("https://github.com/rezamahrm100-ops/" +
                              self.publisher + "/releases/download/v1.2.3/program.exe"),
                "sha256": hashlib.sha256(self.body).hexdigest(),
                "size_bytes": len(self.body)
            },
            "source_repo": self.publisher,
            "source_sha": "b" * 40,
            "package_id": None,
            "version_code": None
        }), encoding="utf-8")

    def shutdown(self):
        self.server.shutdown()
        self.server.server_close()
        self.worker.join(timeout=5)

    def test_verified_tls_probe_is_reachable_without_publisher_token(self):
        found = client.probe(self.details)
        self.assertTrue(found["tls_pinned"])
        self.assertTrue(found["quarantine_api_reachable"])
        self.assertFalse(found["publisher_token_authenticated"])
        self.assertFalse(found["production_release_authorized"])
        self.assertEqual(list(self.quarantine.iterdir()), [])

    def test_exact_authenticated_bytes_reach_real_private_quarantine(self):
        profile = {"schema_version": 1, "details": self.details,
                   "encrypted_token": base64.b64encode(b"one-run-only").decode("ascii")}
        with patch.object(client, "read_profile", return_value=profile), \
             patch.object(client, "_dpapi", return_value=self.token.encode("ascii")):
            receipt = client.submit(self.candidate, self.artifact)
        self.assertEqual(receipt["status"], "quarantined")
        self.assertFalse(receipt["production_release_authorized"])
        folder, proof = inbox.load(self.quarantine, receipt["submission_id"])
        self.assertEqual((folder / "candidate.exe").read_bytes(), self.body)
        self.assertFalse(proof["production_distribution_authorized"])

    def test_wrong_tls_leaf_pin_blocks_before_token_access(self):
        bad = dict(self.details, server_cert_sha256="f" * 64)
        profile = {"schema_version": 1, "details": bad,
                   "encrypted_token": base64.b64encode(b"not-a-real-secret").decode("ascii")}
        with patch.object(client, "read_profile", return_value=profile), \
             patch.object(client, "_dpapi") as decrypt:
            with self.assertRaises(client.ConfigurationError):
                client.submit(self.candidate, self.artifact)
            decrypt.assert_not_called()
        self.assertEqual(list(self.quarantine.iterdir()), [])

    def test_modified_binary_fails_before_issuing_network_request(self):
        self.artifact.write_bytes(self.body + b"modified")
        with patch.object(client, "_connection") as network:
            with self.assertRaises(client.ConfigurationError):
                client.validate_candidate(self.candidate, self.artifact, self.publisher)
            network.assert_not_called()
        self.assertEqual(list(self.quarantine.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
