import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import release_history as h
import release_review
import publisher_gate


class ContinuityTests(unittest.TestCase):
    def setUp(self):
        self.raw = b"test signed fixture placeholder, not a real apk"
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "demo.apk"
        self.path.write_bytes(self.raw)
        self.cert = "a" * 64
        self.sha = hashlib.sha256(self.raw).hexdigest()
        self.registry = {
            "schema_version": 1,
            "publishers": [{"app_id": "demo", "source_repo": "demo-project",
                            "platform": "android", "certificate_sha256": self.cert,
                            "package_id": "ir.hamapp.demo"}]}
        self.c = {
            "release": {
                "app_id": "demo", "platform": "android", "version": "2.0.0",
                "asset_url": "https://github.com/rezamahrm100-ops/demo-project/releases/download/v2.0.0/demo.apk",
                "sha256": self.sha, "size_bytes": len(self.raw)},
            "source_repo": "demo-project", "source_sha": "b" * 40,
            "package_id": "ir.hamapp.demo", "version_code": 20}
        self.history = {"schema_version": 1, "releases": [], "revoked_signers": []}

    def older(self, **updates):
        obj = {"app_id": "demo", "platform": "android", "version": "1.9.0",
               "version_code": 19, "source_repo": "demo-project", "package_id": "ir.hamapp.demo",
               "certificate_sha256": self.cert, "artifact_sha256": "f" * 64, "status": "approved"}
        obj.update(updates)
        return obj

    def test_empty_ledger_is_valid(self):
        self.assertEqual(h.validate_history(self.history)["releases"], [])
        self.assertEqual(h.check_continuity(self.c, self.registry, self.history)["status"], "pending")

    def test_checked_in_history_has_safe_defaults(self):
        data = json.loads((ROOT / "catalog/release_history.json").read_text(encoding="utf-8"))
        self.assertEqual(h.validate_history(data), self.history)

    def test_reviewed_history_can_advance(self):
        self.history["releases"].append(self.older())
        self.assertEqual(h.check_continuity(self.c, self.registry, self.history)["version"], "2.0.0")

    def test_semver_prerelease_precedence(self):
        self.assertLess(h.semver_key("1.2.3-alpha.1"), h.semver_key("1.2.3-alpha.2"))
        self.assertLess(h.semver_key("1.2.3-alpha.3"), h.semver_key("1.2.3"))
        self.assertLess(h.semver_key("1.2.3-1"), h.semver_key("1.2.3-alpha"))

    def test_semver_leading_zero_rejected(self):
        for v in ("01.2.3", "1.02.3", "1.2.3-01", "v1.2.3", "1.2.3+build"):
            with self.subTest(version=v), self.assertRaises(h.HistoryError):
                h.semver_key(v)

    def test_version_rollback_blocked(self):
        self.history["releases"].append(self.older(version="2.1.0"))
        with self.assertRaisesRegex(h.HistoryError, "version rollback"):
            h.check_continuity(self.c, self.registry, self.history)

    def test_same_version_replay_blocked(self):
        self.history["releases"].append(self.older(version="2.0.0"))
        with self.assertRaisesRegex(h.HistoryError, "version rollback"):
            h.check_continuity(self.c, self.registry, self.history)

    def test_android_code_rollback_blocked(self):
        self.history["releases"].append(self.older(version_code=20))
        with self.assertRaisesRegex(h.HistoryError, "versionCode rollback"):
            h.check_continuity(self.c, self.registry, self.history)

    def test_revoked_release_still_blocks_rollback(self):
        self.history["releases"].append(self.older(version="2.1.0", status="revoked"))
        with self.assertRaises(h.HistoryError):
            h.check_continuity(self.c, self.registry, self.history)

    def test_revoked_certificate_blocks_all_versions(self):
        self.history["revoked_signers"].append(self.cert)
        with self.assertRaisesRegex(h.HistoryError, "revoked"):
            h.check_continuity(self.c, self.registry, self.history)

    def test_certificate_substitution_rejected(self):
        self.history["releases"].append(self.older(certificate_sha256="c" * 64))
        with self.assertRaisesRegex(h.HistoryError, "identity changed"):
            h.check_continuity(self.c, self.registry, self.history)

    def test_source_identity_substitution_rejected(self):
        self.history["releases"].append(self.older(source_repo="other-repo"))
        with self.assertRaisesRegex(h.HistoryError, "identity changed"):
            h.check_continuity(self.c, self.registry, self.history)

    def test_hash_replay_rejected(self):
        self.history["releases"].append(self.older(artifact_sha256=self.sha))
        with self.assertRaisesRegex(h.HistoryError, "artifact replay"):
            h.check_continuity(self.c, self.registry, self.history)

    def test_duplicate_version_history_rejected(self):
        self.history["releases"] = [self.older(), self.older(artifact_sha256="e" * 64)]
        with self.assertRaisesRegex(h.HistoryError, "duplicate recorded version"):
            h.validate_history(self.history)

    def test_unapproved_history_record_rejected(self):
        self.history["releases"].append(self.older(status="pending"))
        with self.assertRaises(h.HistoryError):
            h.validate_history(self.history)

    def test_bool_version_code_rejected(self):
        self.history["releases"].append(self.older(version_code=True))
        with self.assertRaises(h.HistoryError):
            h.validate_history(self.history)

    def test_duplicate_revoked_fingerprint_rejected(self):
        self.history["revoked_signers"] = [self.cert, self.cert]
        with self.assertRaises(h.HistoryError):
            h.validate_history(self.history)

    def test_false_receipt_cannot_authorize(self):
        class Runner:
            def __call__(self, command, **kwargs):
                import subprocess
                if command[0] == "apksigner":
                    raw = "Signer #1 certificate SHA-256 digest: " + self_cert + "\n"
                else:
                    raw = "package: name='ir.hamapp.demo' versionCode='20' versionName='2.0.0'\n"
                return subprocess.CompletedProcess(command, 0, raw, "")
        self_cert = self.cert
        review = release_review.prepare_review(self.c, self.registry, self.history, self.path, runner=Runner())
        self.assertFalse(review["public_release_authorized"])
        self.assertFalse(review["history_changed"])
        self.assertFalse(review["source_commit_verified"])
        self.assertTrue(review["candidate_verification"]["signature_verified"])

    def test_wrong_signer_fails_real_review(self):
        class Runner:
            def __call__(self, command, **kwargs):
                import subprocess
                if command[0] == "apksigner":
                    raw = "Signer #1 certificate SHA-256 digest: " + "c" * 64 + "\n"
                else:
                    raw = "package: name='ir.hamapp.demo' versionCode='20' versionName='2.0.0'\n"
                return subprocess.CompletedProcess(command, 0, raw, "")
        with self.assertRaises(publisher_gate.PublisherError):
            release_review.prepare_review(self.c, self.registry, self.history, self.path, runner=Runner())

    def test_windows_new_version_requires_increasing_semver(self):
        self.registry["publishers"] = [{"app_id": "demo", "source_repo": "demo-project",
                                        "platform": "windows", "certificate_sha256": self.cert,
                                        "package_id": None}]
        self.c["package_id"] = None
        self.c["version_code"] = None
        self.c["release"]["platform"] = "windows"
        self.c["release"]["asset_url"] = self.c["release"]["asset_url"].replace(".apk", ".msix")
        self.history["releases"] = [self.older(platform="windows", package_id=None,
                                               version_code=None, version="2.1.0")]
        with self.assertRaises(h.HistoryError):
            h.check_continuity(self.c, self.registry, self.history)


if __name__ == "__main__":
    unittest.main()
