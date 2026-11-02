import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("release_integrity", ROOT / "scripts/release_integrity.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ReleaseIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.data = b"test release candidate only\n"
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.file = Path(self.tmp.name) / "app.apk"
        self.file.write_bytes(self.data)
        self.m = {
            "app_id": "my-app", "platform": "android", "version": "1.2.3",
            "asset_url": "https://github.com/rezamahrm100-ops/example/releases/download/v1.2.3/app.apk",
            "sha256": hashlib.sha256(self.data).hexdigest(), "size_bytes": len(self.data),
        }

    def test_valid_receipt_explicitly_excludes_signature(self):
        result = module.verify_file(self.m, self.file)
        self.assertEqual(result["integrity"], "hash-and-size-verified")
        self.assertFalse(result["signature_verified"])

    def test_modified_asset_rejected(self):
        self.file.write_bytes(b"X" + self.data[1:])
        with self.assertRaisesRegex(module.IntegrityError, "sha256 mismatch"):
            module.verify_file(self.m, self.file)

    def test_size_mismatch_rejected(self):
        self.m["size_bytes"] += 1
        with self.assertRaisesRegex(module.IntegrityError, "size mismatch"):
            module.verify_file(self.m, self.file)

    def test_fake_host_rejected(self):
        self.m["asset_url"] = self.m["asset_url"].replace("github.com/", "github.com.attacker.test/")
        with self.assertRaises(module.IntegrityError):
            module.validate_manifest(self.m)

    def test_query_rejected(self):
        self.m["asset_url"] += "?unsafe=1"
        with self.assertRaises(module.IntegrityError):
            module.validate_manifest(self.m)

    def test_version_tag_mismatch_rejected(self):
        self.m["asset_url"] = self.m["asset_url"].replace("v1.2.3", "v9.0.0")
        with self.assertRaises(module.IntegrityError):
            module.validate_manifest(self.m)

    def test_cross_platform_extension_rejected(self):
        self.m["asset_url"] = self.m["asset_url"].replace(".apk", ".exe")
        with self.assertRaises(module.IntegrityError):
            module.validate_manifest(self.m)

    def test_unexpected_publisher_claim_rejected(self):
        self.m["signature_verified"] = True
        with self.assertRaises(module.IntegrityError):
            module.validate_manifest(self.m)

    def test_bool_size_rejected(self):
        self.m["size_bytes"] = True
        with self.assertRaises(module.IntegrityError):
            module.validate_manifest(self.m)

    def test_symlink_rejected(self):
        link = Path(self.tmp.name) / "link"
        try:
            link.symlink_to(self.file)
        except OSError:
            self.skipTest("symlink unavailable")
        with self.assertRaises(module.IntegrityError):
            module.verify_file(self.m, link)

    def test_encoded_separator_rejected(self):
        self.m["asset_url"] = self.m["asset_url"].replace("example", "exa%2Fmple")
        with self.assertRaises(module.IntegrityError):
            module.validate_manifest(self.m)

    def test_windows_extension_acceptance(self):
        self.m["platform"] = "windows"
        self.m["asset_url"] = self.m["asset_url"].replace(".apk", ".msix")
        self.assertEqual(module.validate_manifest(self.m)["platform"], "windows")


if __name__ == "__main__":
    unittest.main()
