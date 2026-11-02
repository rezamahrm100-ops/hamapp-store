import hashlib
import pathlib
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import owner_candidate_intake as intake

class OwnerIntakeTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.apk = pathlib.Path(t.name) / "example.apk"
        with zipfile.ZipFile(self.apk, "w", compression=zipfile.ZIP_DEFLATED) as f:
            f.writestr("classes.dex", b"test only")
        self.sha = hashlib.sha256(self.apk.read_bytes()).hexdigest()
        self.candidate = {"release": {"app_id": "example", "platform": "android",
                           "version": "1.2.3", "sha256": self.sha,
                           "size_bytes": self.apk.stat().st_size},
                          "package_id": "ir.example.app", "version_code": 7,
                          "source_sha": "a" * 40}
        self.policy = {"schema_version": 1, "package_id": "ir.example.app",
                       "version_code": 7, "version_name": "1.2.3",
                       "allowed_permissions": []}
        self.review = {
            "candidate_release": {"artifact_sha256": self.sha},
            "verified_artifact_sha256": self.sha,
            "public_distribution_authorized": False
        }

    def call(self, **options):
        return intake.assess(self.candidate, {"schema_version": 1, "publishers": []},
                             {"schema_version": 1, "releases": [], "revoked_signers": []},
                             self.apk, "approved/workflow", "refs/tags/v1.2.3",
                             permission_policy=self.policy, **options)

    def test_valid_real_archive_with_mocked_cryptography_is_review_only(self):
        from types import SimpleNamespace
        def aapt(cmd, **kwargs):
            out = ("package: name='ir.example.app' versionCode='7' versionName='1.2.3'\n"
                   if cmd[2] == "badging" else "package: ir.example.app\n")
            return SimpleNamespace(returncode=0, stdout=out)
        with patch.object(intake.release_governance, "plan_promotion", return_value=self.review):
            r = self.call(aapt_runner=aapt)
        self.assertEqual(r["actual_archive"]["artifact_sha256"], self.sha)
        self.assertEqual(r["actual_android_permissions"]["requested_permissions"], [])
        self.assertTrue(r["developer_signature_and_github_provenance_checked"])
        self.assertFalse(r["malware_signature_and_behavior_clearance"])
        self.assertFalse(r["public_distribution_authorized"])
        self.assertFalse(r["files_committed"])

    def test_owner_intake_rejects_antivirus_digest_mismatch(self):
        from types import SimpleNamespace
        def aapt(cmd, **kwargs):
            out = ("package: name='ir.example.app' versionCode='7' versionName='1.2.3'\n"
                   if cmd[2] == "badging" else "package: ir.example.app\n")
            return SimpleNamespace(returncode=0, stdout=out)
        with patch.object(intake.release_governance, "plan_promotion", return_value=self.review), \
             patch.object(intake.antivirus_binary_review, "scan",
                          return_value={"artifact_sha256": "d" * 64}):
            with self.assertRaises(intake.IntakeError):
                self.call(aapt_runner=aapt, antivirus_scanner="clamscan")

    def test_owner_intake_can_record_actual_scanner_receipt_without_public_approval(self):
        from types import SimpleNamespace
        def aapt(cmd, **kwargs):
            out = ("package: name='ir.example.app' versionCode='7' versionName='1.2.3'\n"
                   if cmd[2] == "badging" else "package: ir.example.app\n")
            return SimpleNamespace(returncode=0, stdout=out)
        malware_receipt = {"artifact_sha256": self.sha,
                           "actual_signature_scan_completed_without_detection": True,
                           "malware_absence_verified": False}
        with patch.object(intake.release_governance, "plan_promotion", return_value=self.review), \
             patch.object(intake.antivirus_binary_review, "scan", return_value=malware_receipt):
            result = self.call(aapt_runner=aapt, antivirus_scanner="clamscan")
        self.assertEqual(result["actual_antivirus_signature_scan"], malware_receipt)
        self.assertFalse(result["malware_signature_and_behavior_clearance"])
        self.assertFalse(result["public_distribution_authorized"])

    def test_missing_policy_cannot_pass(self):
        with patch.object(intake.release_governance, "plan_promotion", return_value=self.review):
            with self.assertRaises(intake.IntakeError):
                intake.assess(self.candidate, {}, {}, self.apk, "w", "ref")

    def test_replaced_archive_fails_after_promotion_preflight(self):
        original = self.apk.read_bytes()
        def poison(*args, **kwargs):
            self.apk.write_bytes(b"mutated after upstream verification")
            return self.review
        with patch.object(intake.release_governance, "plan_promotion", side_effect=poison):
            with self.assertRaises(intake.binary_archive_review.ArchiveReviewError):
                self.call()
        self.assertNotEqual(self.apk.read_bytes(), original)

    def test_mismatched_claim_rejected(self):
        with patch.object(intake.release_governance, "plan_promotion",
                          return_value=dict(self.review, verified_artifact_sha256="f" * 64)):
            with self.assertRaises(intake.IntakeError):
                self.call()

    def test_unknown_windows_policy_rejected(self):
        self.candidate["release"]["platform"] = "windows"
        windows = self.apk.with_suffix(".exe")
        windows.write_bytes(b"unsigned test executable")
        with patch.object(intake.release_governance, "plan_promotion",
                          return_value=self.review):
            with self.assertRaises(intake.IntakeError):
                intake.assess(self.candidate, {}, {}, windows, "w", "ref",
                              permission_policy=self.policy)

if __name__ == "__main__":
    unittest.main()
