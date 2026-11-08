"""Owner-preview test artifact packaging: deterministic hashes and fail-closed inputs."""
import hashlib
import json
import tempfile
from pathlib import Path
import sys
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import package_owner_preview as preview

SHA = "a" * 40


class OwnerPreviewDeliveryTests(unittest.TestCase):
    def make_android(self, root):
        file = root / preview.PRODUCTS["android"][0]
        with zipfile.ZipFile(file, "w") as z:
            z.writestr("AndroidManifest.xml", b"binary AndroidManifest placeholder" * 60)
            z.writestr("classes.dex", b"dex" * 500)
        return file

    def make_windows(self, root):
        files = []
        for name in preview.PRODUCTS["windows"]:
            file = root / name
            file.write_bytes(b"MZ" + bytes(1600) + name.encode("utf-8"))
            files.append(file)
        return files

    def test_android_delivery_receipt_matches_zip_bytes_and_shows_no_prod_claim(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            apk = self.make_android(root)
            receipt = preview.write_delivery(root, "android", SHA)
            self.assertEqual(receipt["source_commit"], SHA)
            self.assertEqual(receipt["platform"], "android")
            self.assertEqual(receipt["build_files"][0]["sha256"],
                             hashlib.sha256(apk.read_bytes()).hexdigest())
            self.assertFalse(receipt["production_signed"])
            self.assertFalse(receipt["owner_device_tested"])
            self.assertFalse(receipt["public_release_authorized"])
            self.assertFalse(receipt["third_party_downloads_enabled"])
            self.assertEqual(json.loads((root / "manifest.json").read_text("utf-8")),
                             receipt)
            self.assertIn(apk.name, (root / "SHA256SUMS.txt").read_text())
            self.assertIn("Debug", (root / "README_FA.md").read_text("utf-8"))
            with self.assertRaisesRegex(preview.DeliveryError, "overwrite"):
                preview.write_delivery(root, "android", SHA)

    def test_windows_setup_and_portable_exe_both_have_distinct_sha(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            files = self.make_windows(root)
            receipt = preview.write_delivery(root, "windows", SHA)
            self.assertEqual(len(receipt["build_files"]), 2)
            for i, file in enumerate(files):
                self.assertEqual(receipt["build_files"][i]["sha256"],
                                 hashlib.sha256(file.read_bytes()).hexdigest())
            self.assertNotEqual(receipt["build_files"][0]["sha256"],
                                receipt["build_files"][1]["sha256"])
            self.assertIn("UNSIGNED", (root / "README_FA.md").read_text("utf-8"))

    def test_reject_missing_malformed_wrong_sha_or_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self.make_android(root)
            with self.assertRaises(preview.DeliveryError):
                preview.inspect(root, "android", "not-a-source-sha")
            with self.assertRaises(preview.DeliveryError):
                preview.inspect(root, "windows", SHA)
            with self.assertRaises(preview.DeliveryError):
                preview.inspect(root, "other", SHA)
            apk = root / preview.PRODUCTS["android"][0]
            apk.unlink()
            apk.write_bytes(b"PK" + bytes(2048))
            with self.assertRaisesRegex(preview.DeliveryError, "ZIP"):
                preview.inspect(root, "android", SHA)
            apk.unlink()
            original = root / "valid.zip"
            with zipfile.ZipFile(original, "w") as z:
                z.writestr("AndroidManifest.xml", b"x" * 1500)
            try:
                apk.symlink_to(original)
            except OSError as exc:
                if getattr(exc, "winerror", None) == 1314:
                    self.skipTest("Windows runner lacks symlink privilege; hosted POSIX covers link rejection")
                raise
            with self.assertRaisesRegex(preview.DeliveryError, "linked"):
                preview.inspect(root, "android", SHA)

    def test_source_guards_and_non_release_disclosure(self):
        script = (Path(__file__).resolve().parents[1] / "scripts" /
                  "package_owner_preview.py").read_text("utf-8")
        self.assertIn('"GITHUB_ACTIONS"', script)
        self.assertIn('"GITHUB_REPOSITORY"', script)
        self.assertIn('"GITHUB_SHA"', script)
        self.assertIn('"production_signed": False', script)
        self.assertIn('"public_release_authorized": False', script)
        self.assertIn('"owner_device_tested": False', script)
        self.assertNotIn("gh release create", script)


if __name__ == "__main__":
    unittest.main()
