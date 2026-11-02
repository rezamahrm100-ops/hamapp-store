import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_evidence", ROOT / "scripts/build_evidence.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.site = self.dir / "site"
        (self.site / "catalog").mkdir(parents=True)
        for name in ("index.html", "app.js", "sw.js", "catalog/apps.json"):
            (self.site / name).write_bytes(("asset: " + name).encode("utf-8"))

    def test_identical_bytes_for_same_source(self):
        first = self.dir / "first.zip"
        second = self.dir / "second.zip"
        self.assertEqual(module.archive_site(self.site, first), 4)
        self.assertEqual(module.archive_site(self.site, second), 4)
        self.assertEqual(first.read_bytes(), second.read_bytes())
        with zipfile.ZipFile(first) as bundle:
            self.assertEqual(sorted(bundle.namelist()), ["app.js", "catalog/apps.json", "index.html", "sw.js"])

    def test_receipt_excludes_app_signature_claims(self):
        output = self.dir / "evidence"
        receipt = module.evidence(self.site, output, "0" * 40)
        self.assertFalse(receipt["production_store_ready"])
        self.assertIn("APK signing certificate", receipt["not_verified"])
        self.assertEqual(receipt["sha256"], hashlib.sha256(
            (output / "hamapp-static-site.zip").read_bytes()).hexdigest())
        self.assertEqual(json.loads((output / "static-site-evidence.json").read_text())["sha256"],
                         receipt["sha256"])

    def test_missing_core_asset_fails(self):
        (self.site / "app.js").unlink()
        with self.assertRaises(ValueError):
            module.archive_site(self.site, self.dir / "bad.zip")

    def test_symlink_rejected(self):
        link = self.site / "link"
        try:
            link.symlink_to(self.site / "index.html")
        except (OSError, NotImplementedError):
            self.skipTest("no symlink permission")
        with self.assertRaises(ValueError):
            module.archive_site(self.site, self.dir / "bad.zip")

    def test_nested_destination_rejected(self):
        with self.assertRaises(ValueError):
            module.archive_site(self.site, self.site / "inside.zip")


if __name__ == "__main__":
    unittest.main()
