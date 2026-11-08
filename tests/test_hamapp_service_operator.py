"""Actual owner-private service lifecycle and deterministic offline kit.

No production credentials, real user installs or publisher identities are
invented. Disposable OpenSSL localhost certificate is strictly a CI fixture.
"""
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import hamapp_operator as operator
import build_service_kit as pack
import publisher_intake_service as intake
import remote_publisher_tls_service as tls


@unittest.skipUnless(os.name == "posix" and shutil.which("openssl"),
                     "POSIX owner-only storage and real OpenSSL required")
class PrivateServiceOperationalTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="hamapp-private-service-test-")
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.private = self.dir / "data"
        self.publisher = "review-publisher"
        self.cert, self.key = operator.local_development_certificate()

    def test_real_provision_token_rotation_revocation_cert_and_tls_socket(self):
        proof = operator.bootstrap(
            self.private, self.publisher, public_cert=self.cert,
            private_key=self.key, local_development=True)
        self.assertTrue(proof["ready_for_private_quarantine"])
        self.assertFalse(proof["public_release_authorized"])
        self.assertEqual(len(proof["one_time_token"]), 64)
        self.assertEqual((self.private / "tls-key.pem").stat().st_mode & 0o077, 0)
        self.assertEqual((self.private / "credentials.json").stat().st_mode & 0o077, 0)
        record = json.loads((self.private / "credentials.json").read_text("utf-8"))
        self.assertNotIn(proof["one_time_token"], str(record))
        self.assertEqual(record["publishers"][0]["token_sha256"],
                         hashlib.sha256(proof["one_time_token"].encode("ascii")).hexdigest())

        status = operator.check(self.private)
        self.assertTrue(status["tls_chain_loaded"])
        self.assertEqual(status["publisher_token_slots"], 1)
        self.assertTrue(status["local_development_only"])
        self.assertFalse(status["public_store_deployed"])
        rotation = operator.change(self.private, "rotate", self.publisher)
        self.assertNotEqual(rotation["one_time_secret"], proof["one_time_token"])
        self.assertNotIn(rotation["one_time_secret"],
                         (self.private / "credentials.json").read_text("utf-8"))

        # A real, pinned TLS server can start from the provisioned private
        # operator data without changing a single repository source file.
        server = tls.TLSQuarantineServer(
            self.private / "inbox", self.private / "incoming",
            self.private / "credentials.json", self.private / "tls-cert.pem",
            self.private / "tls-key.pem")
        thread = threading.Thread(target=server.serve_forever,
                                  kwargs={"poll_interval": 0.1}, daemon=True)
        thread.start()
        try:
            context = ssl.create_default_context(cafile=str(self.private / "tls-cert.pem"))
            context.minimum_version = ssl.TLSVersion.TLSv1_2
            with socket.create_connection(("127.0.0.1", server.server_port), timeout=8) as sock:
                with context.wrap_socket(sock, server_hostname="localhost") as verified:
                    digest = hashlib.sha256(verified.getpeercert(binary_form=True)).hexdigest()
                    self.assertEqual(digest, proof["tls_leaf_sha256"])
                    verified.sendall(b"GET /v1/submissions HTTP/1.0\r\nHost: localhost\r\n\r\n")
                    response = verified.recv(256)
                    self.assertIn(b"405", response)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=8)
        operator.change(self.private, "revoke", self.publisher)
        self.assertEqual(operator.check(self.private)["publisher_token_slots"], 0)

    def test_private_cli_never_logs_supplied_token(self):
        secret = b"V" * 64
        cmd = [sys.executable, str(ROOT / "scripts/hamapp_operator.py"),
               "init", "--root", str(self.private), "--publisher", self.publisher,
               "--dev-local-cert", "--token-stdin"]
        result = subprocess.run(cmd, input=secret, capture_output=True, timeout=40)
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", errors="replace"))
        self.assertNotIn(secret, result.stdout)
        self.assertNotIn(secret, result.stderr)
        self.assertEqual(json.loads((self.private / "credentials.json").read_text("utf-8"))
                         ["publishers"][0]["token_sha256"], hashlib.sha256(secret).hexdigest())
        denied = subprocess.run(cmd, input=secret, capture_output=True, timeout=40)
        self.assertNotEqual(denied.returncode, 0)
        self.assertNotIn(secret, denied.stdout + denied.stderr)

    def test_duplicate_service_provision_refused_without_overwrite(self):
        operator.bootstrap(self.private, self.publisher,
                           public_cert=self.cert, private_key=self.key)
        before = (self.private / "credentials.json").read_bytes()
        with self.assertRaises(operator.OperatorError):
            operator.bootstrap(self.private, self.publisher,
                               public_cert=self.cert, private_key=self.key)
        self.assertEqual((self.private / "credentials.json").read_bytes(), before)

    def test_wrong_key_or_unsafe_private_root_refused(self):
        with self.assertRaises((ValueError, ssl.SSLError)):
            operator.bootstrap(self.private, self.publisher, public_cert=self.cert,
                               private_key=self.cert)
        self.assertFalse(self.private.exists())
        external = self.dir / "external"
        external.mkdir()
        shortcut = self.dir / "data-link"
        shortcut.symlink_to(external, target_is_directory=True)
        with self.assertRaises(operator.OperatorError):
            operator.bootstrap(shortcut, self.publisher, public_cert=self.cert,
                               private_key=self.key)

    def test_length_prefixed_secret_stdin_envelope_enforced(self):
        import io
        import struct
        valid = struct.pack("!II", len(self.cert), len(self.key)) + self.cert + self.key
        self.assertEqual(operator.load_pem_stdin(io.BytesIO(valid)), (self.cert, self.key))
        token = b"A" * 64
        self.assertEqual(operator.load_pem_stdin(io.BytesIO(valid + token), with_token=True),
                         (self.cert, self.key, token.decode("ascii")))
        with self.assertRaises(operator.OperatorError):
            operator.load_pem_stdin(io.BytesIO(valid + token + b"x"), with_token=True)
        with self.assertRaises(operator.OperatorError):
            operator.read_token_stdin(io.BytesIO(token + b"x"))
        for broken in (b"", valid[:-1], valid + b"x", b"\x00" * 8):
            with self.assertRaises(operator.OperatorError):
                operator.load_pem_stdin(io.BytesIO(broken))


class SafeServiceKitTests(unittest.TestCase):
    def test_single_reproducible_service_bundle_contains_no_secret_keys(self):
        with tempfile.TemporaryDirectory(prefix="hamapp-service-kit-") as folder:
            path1 = Path(folder) / "first.zip"
            path2 = Path(folder) / "second.zip"
            source = "a" * 40
            proof = pack.build(path1, source_sha=source)
            pack.build(path2, source_sha=source)
            self.assertEqual(path1.read_bytes(), path2.read_bytes())
            self.assertFalse(proof["public_distribution_authorized"]
                             if "public_distribution_authorized" in proof else
                             proof["production_signed"])
            with zipfile.ZipFile(path1) as z:
                names = z.namelist()
                self.assertIn("deployment/compose.yaml", names)
                self.assertIn("scripts/hamapp_operator.py", names)
                self.assertIn("windows_client/publisher_connection.py", names)
                self.assertIn("deployment/HamApp-Service-Setup.cmd", names)
                for name in names:
                    self.assertNotIn("..", Path(name).parts)
                    self.assertFalse(name.lower().endswith(
                        (".key", ".jks", ".pem", ".pfx", ".env")))
                manifest = json.loads(z.read("service-kit-manifest.json"))
                self.assertEqual(manifest["source_sha"], source)
                self.assertFalse(manifest["production_signed"])
                self.assertFalse(manifest["public_distribution_authorized"])
                with self.assertRaises(pack.KitError):
                    pack.build(path1, source_sha=source)

    def test_container_is_private_nonroot_and_engine_scope_is_single(self):
        dockerfile = (ROOT / "deployment/Dockerfile").read_text("utf-8")
        compose = (ROOT / "deployment/compose.yaml").read_text("utf-8")
        self.assertIn("USER 10001:10001", dockerfile)
        self.assertIn("cap_drop:", compose)
        self.assertIn("read_only: true", compose)
        self.assertIn("127.0.0.1:", compose)
        self.assertIn("hamapp_private:", compose)
        self.assertNotIn("privileged: true", compose)
        self.assertNotIn("docker.sock", compose)
        self.assertNotIn("network_mode: host", compose)
        self.assertNotIn("docker prune", compose)


if __name__ == "__main__":
    unittest.main()
