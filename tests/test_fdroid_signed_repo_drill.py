import importlib.util
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

    def test_signing_assets_not_checked_into_public_project(self):
        for pattern in ("**/keystore.p12", "**/keystore.jks", "**/config-secret.yml"):
            self.assertFalse(list(ROOT.glob(pattern)), pattern)


if __name__ == "__main__":
    unittest.main()
