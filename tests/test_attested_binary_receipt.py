import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("attested_binary_receipt", ROOT / "scripts/attested_binary_receipt.py")
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)


class AttestedBinaryReceiptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "app-debug.apk"
        self.path.write_bytes(b"untrusted mock fixture not a real signed APK")
        self.digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
        self.sha = "a" * 40

    def verified(self, name="app-debug.apk", digest=None, predicate=None):
        return [{"verificationResult": {"statement": {
            "predicateType": predicate or verify.PREDICATE,
            "subject": [{"name": name, "digest": {"sha256": digest or self.digest}}]
        }}}]

    def test_review_receipt_never_grants_release(self):
        receipt = verify.make_receipt(self.path, self.verified(), "android-debug", self.sha)
        self.assertEqual(receipt["sha256"], self.digest)
        self.assertTrue(receipt["github_build_provenance_checked"])
        for key in ("android_release_key_verified", "windows_authenticode_verified",
                    "fdroid_repo_index_signature_verified", "owner_approved_for_distribution",
                    "device_install_upgrade_verified", "production_ready"):
            self.assertFalse(receipt[key])

    def test_wrong_byte_digest_rejected(self):
        with self.assertRaises(verify.EvidenceError):
            verify.make_receipt(self.path, self.verified(digest="b" * 64), "android-debug", self.sha)

    def test_wrong_binary_name_rejected(self):
        with self.assertRaises(verify.EvidenceError):
            verify.make_receipt(self.path, self.verified(name="evil.apk"), "android-debug", self.sha)

    def test_non_slsa_predicate_rejected(self):
        with self.assertRaises(verify.EvidenceError):
            verify.make_receipt(self.path, self.verified(predicate="https://spdx.dev/Document/v2.3"),
                                "android-debug", self.sha)

    def test_unverified_result_rejected(self):
        for invalid in (None, [], {}, ["ok"], [{"verificationResult": {}}]):
            with self.subTest(invalid=invalid), self.assertRaises(verify.EvidenceError):
                verify.make_receipt(self.path, invalid, "android-debug", self.sha)

    def test_non_full_commit_rejected(self):
        with self.assertRaises(verify.EvidenceError):
            verify.make_receipt(self.path, self.verified(), "android-debug", "refs/heads/main")

    def test_empty_binary_rejected(self):
        self.path.write_bytes(b"")
        with self.assertRaises(verify.EvidenceError):
            verify.make_receipt(self.path, self.verified(), "android-debug", self.sha)

    def test_symlink_rejected(self):
        fake = Path(self.tmp.name) / "other.apk"
        try:
            fake.symlink_to(self.path)
        except (OSError, NotImplementedError):
            self.skipTest("symlink unavailable")
        with self.assertRaises(verify.EvidenceError):
            verify.make_receipt(fake, self.verified(), "android-debug", self.sha)

    def test_windows_role_is_separate(self):
        with self.assertRaises(verify.EvidenceError):
            verify.make_receipt(self.path, self.verified(), "windows-unsigned", self.sha)
        exe = Path(self.tmp.name) / "HamApp-Windows-Preview.exe"
        exe.write_bytes(self.path.read_bytes())
        receipt = verify.make_receipt(exe, self.verified(name=exe.name), "windows-unsigned", self.sha)
        self.assertFalse(receipt["windows_authenticode_verified"])

    def test_relative_subject_path_accepted(self):
        receipt = verify.make_receipt(self.path, self.verified(name="dist/native-artifact/app-debug.apk"),
                                      "android-debug", self.sha)
        self.assertEqual(receipt["size_bytes"], len(self.path.read_bytes()))


if __name__ == "__main__":
    unittest.main()
