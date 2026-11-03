import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("fdroid_signed_repo_drill", ROOT / "scripts/fdroid_signed_repo_drill.py")
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


class SignedRepoDrillPolicyTests(unittest.TestCase):
    def setUp(self):
        self.sha = "a" * 40
        self.fp = "B" * 64

    def test_safe_receipt_has_strictly_negative_production_claims(self):
        receipt = d.public_receipt(self.sha, self.fp, {
            "indexed_packages": 1, "expected_package_listed": True
        }, True, True)
        for key in ("temporary_key_is_production", "production_repo_key_created",
                    "production_repo_index_signed", "production_publication_performed",
                    "approved_app_installed_or_updated", "production_ready"):
            self.assertIs(receipt[key], False)
        self.assertTrue(receipt["signed_index_verified_with_temporary_fingerprint"])
        self.assertTrue(receipt["tampered_index_rejected"])
        self.assertTrue(receipt["wrong_fingerprint_rejected"])
        self.assertNotIn("keystorepass", receipt)

    def test_no_false_receipt_without_wrong_fingerprint_rejection(self):
        with self.assertRaises(d.DrillError):
            d.public_receipt(self.sha, self.fp, {}, False, True)

    def test_no_false_receipt_without_tampering_rejection(self):
        with self.assertRaises(d.DrillError):
            d.public_receipt(self.sha, self.fp, {}, True, False)

    def test_no_short_source_sha(self):
        with self.assertRaises(d.DrillError):
            d.public_receipt("main", self.fp, {}, True, True)

    def test_no_invalid_fingerprint(self):
        with self.assertRaises(d.DrillError):
            d.public_receipt(self.sha, "testing", {}, True, True)

    def test_reject_missing_package_even_if_index_valid(self):
        with self.assertRaises(d.DrillError):
            d.classify_result({"repo": {}, "packages": {}}, "ir.hamapp.store")

    def test_reject_missing_v2_structures(self):
        for val in (None, [], {}, {"repo": {}}, {"packages": {}}, {"repo": {}, "packages": []}):
            with self.subTest(value=val), self.assertRaises(d.DrillError):
                d.classify_result(val, "ir.hamapp.store")

    def test_accept_structurally_signed_package(self):
        r = d.classify_result({"repo": {}, "packages": {"ir.hamapp.store": {}}}, "ir.hamapp.store")
        self.assertEqual(r["indexed_packages"], 1)

    def test_receipt_rejects_forged_production_or_owner_approval(self):
        with self.assertRaises(d.DrillError):
            d.public_receipt(self.sha, self.fp, {
                "indexed_packages": 1, "expected_package_listed": True,
                "production_ready": True
            }, True, True)

    def test_two_version_receipt_requires_actual_continuity_proofs(self):
        two = {
            "indexed_packages": 1, "expected_package_listed": True,
            "actual_debug_version_codes": [1, 2],
            "real_two_version_apk_sha256_distinct": True,
            "same_disposable_repo_certificate_across_two_signed_indexes": True,
            "both_exact_apk_versions_in_fresh_signed_index": True,
            "unapproved_second_version_hash_substitution_rejected": True,
            "official_fdroid_client_subscribed": False,
            "two_version_client_update_performed": False,
            "real_owner_key_restored_or_backed_up": False,
            "actual_ephemeral_keystore_removed_then_restored": True,
            "independent_volume_key_backup_bytes_verified": True,
            "restored_key_material_ephemeral_only": True,
            "restored_ephemeral_key_signed_second_real_index": True,
            "real_owner_backup_or_restore_proven": False
        }
        accepted = d.public_receipt(self.sha, self.fp, two, True, True)
        self.assertTrue(accepted["both_exact_apk_versions_in_fresh_signed_index"])
        self.assertFalse(accepted["production_ready"])
        two["actual_debug_version_codes"] = [2, 1]
        with self.assertRaises(d.DrillError):
            d.public_receipt(self.sha, self.fp, two, True, True)
        two["actual_debug_version_codes"] = [1, 2]
        two["official_fdroid_client_subscribed"] = True
        with self.assertRaises(d.DrillError):
            d.public_receipt(self.sha, self.fp, two, True, True)

        two["official_fdroid_client_subscribed"] = False
        two["restored_ephemeral_key_signed_second_real_index"] = False
        with self.assertRaises(d.DrillError):
            d.public_receipt(self.sha, self.fp, two, True, True)
        two["restored_ephemeral_key_signed_second_real_index"] = True
        two["real_owner_backup_or_restore_proven"] = True
        with self.assertRaises(d.DrillError):
            d.public_receipt(self.sha, self.fp, two, True, True)

    @unittest.skipUnless(os.name == "posix" and Path("/dev/shm").is_dir(),
                         "independent POSIX tmpfs signer recovery test")
    def test_real_disposable_keystore_loss_and_external_volume_restore(self):
        with tempfile.TemporaryDirectory() as base:
            workspace = Path(base) / "fdroid"
            home = Path(base) / "home"
            workspace.mkdir()
            home.mkdir()
            if home.stat().st_dev == Path("/dev/shm").stat().st_dev:
                self.skipTest("no distinct independent temporary filesystem")
            key = home / "repo-test-key.jks"
            key.write_bytes(b"synthetic-not-a-real-key:" + b"R" * 2048)
            key.chmod(0o600)
            before = key.read_bytes()
            report = d.restore_ephemeral_signer_key(
                {"keystore": "~/repo-test-key.jks"}, workspace, home)
            self.assertEqual(key.read_bytes(), before)
            self.assertTrue(report["actual_ephemeral_keystore_removed_then_restored"])
            self.assertTrue(report["independent_volume_key_backup_bytes_verified"])
            self.assertFalse(report["real_owner_backup_or_restore_proven"])
            self.assertEqual(list(Path("/dev/shm").glob("hamapp-fdroid-independent-backup-*")), [])

    @unittest.skipUnless(os.name == "posix" and Path("/dev/shm").is_dir(),
                         "disposable POSIX signer containment guard")
    def test_owner_path_cannot_be_restored_by_disposable_ci_helper(self):
        with tempfile.TemporaryDirectory() as base:
            workspace = Path(base) / "fdroid"
            home = Path(base) / "home"
            workspace.mkdir()
            home.mkdir()
            outsider = Path(base) / "owner-do-not-touch.jks"
            outsider.write_bytes(b"O" * 2048)
            outsider.chmod(0o600)
            with self.assertRaises(d.DrillError):
                d.restore_ephemeral_signer_key({"keystore": str(outsider)}, workspace, home)
            self.assertEqual(outsider.read_bytes(), b"O" * 2048)

    def test_signing_assets_not_checked_into_public_project(self):
        for pattern in ("**/keystore.p12", "**/keystore.jks", "**/config-secret.yml"):
            self.assertFalse(list(ROOT.glob(pattern)), pattern)


if __name__ == "__main__":
    unittest.main()
