import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_android_catalog as builder


class RepoTests(unittest.TestCase):
    def setUp(self):
        self.ok = {"schema_version": 1, "repository": {
            "url": "https://repo.example.org/fdroid/repo/",
            "fingerprint": "a" * 64
        }}

    def test_empty_unpublished_repo_allowed(self):
        self.assertIsNone(builder.validate_repository({"schema_version": 1, "repository": None}))

    def test_config_normalizes_fingerprint(self):
        self.assertEqual(builder.validate_repository(self.ok)["fingerprint"], "A" * 64)

    def test_requires_exact_pinned_fingerprint(self):
        self.ok["repository"]["fingerprint"] = "a" * 63
        with self.assertRaises(ValueError):
            builder.validate_repository(self.ok)

    def test_no_untrusted_http_scheme(self):
        self.ok["repository"]["url"] = "http://repo.example.org/fdroid/repo/"
        with self.assertRaises(ValueError):
            builder.validate_repository(self.ok)

    def test_no_url_credentials(self):
        self.ok["repository"]["url"] = "https://user:pass@repo.example.org/fdroid/repo/"
        with self.assertRaises(ValueError):
            builder.validate_repository(self.ok)

    def test_no_fragment_or_query(self):
        for suffix in ("?fingerprint=unsafe", "#fragment", "/redirect"):
            with self.subTest(suffix=suffix):
                self.ok["repository"]["url"] = "https://repo.example.org/fdroid/repo/" + suffix
                with self.assertRaises(ValueError):
                    builder.validate_repository(self.ok)

    def test_no_encoded_rewrites(self):
        self.ok["repository"]["url"] = "https://repo.example.org/fdroid/%72epo/"
        with self.assertRaises(ValueError):
            builder.validate_repository(self.ok)

    def test_no_extra_config_fields(self):
        self.ok["repository"]["signer_key"] = "fake"
        with self.assertRaises(ValueError):
            builder.validate_repository(self.ok)

    def test_checked_in_repo_is_disabled(self):
        config = json.loads((ROOT / "catalog/android_repository.json").read_text(encoding="utf-8"))
        self.assertIsNone(builder.validate_repository(config))

    def test_build_from_current_store_fails_closed(self):
        catalog = lambda name: json.loads((ROOT / "catalog" / name).read_text(encoding="utf-8"))
        data, config = builder.build(catalog("apps.json"), catalog("trusted_signers.json"),
                                     catalog("release_history.json"), catalog("android_repository.json"))
        self.assertIsNone(config["repository"])
        self.assertTrue(all(x["status"] == "planned" and x["version"] is None for x in data["apps"]))

    def test_builder_does_not_publish(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts/build_android_catalog.py")],
                                cwd=ROOT, text=True, capture_output=True, timeout=40)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads((ROOT / "android/app/src/main/assets/android-catalog.json").read_text("utf-8"))
        self.assertTrue(all(x["status"] == "planned" for x in output["apps"]))

    def test_android_does_not_request_package_install_permission(self):
        manifest = (ROOT / "android/app/src/main/AndroidManifest.xml").read_text("utf-8")
        self.assertNotIn("REQUEST_INSTALL_PACKAGES", manifest)
        self.assertNotIn("android.permission.INTERNET", manifest)
        self.assertIn("android:exported=\"true\"", manifest)

    def test_native_client_delegates_to_fdroid(self):
        src = (ROOT / "android/app/src/main/java/ir/hamapp/store/MainActivity.java").read_text("utf-8")
        engine = (ROOT / "android/app/src/main/java/ir/hamapp/store/FdroidEngine.java").read_text("utf-8")
        self.assertIn("FdroidEngine.requestOpen(this, repo)", src)
        self.assertIn("Intent.ACTION_VIEW", engine)
        self.assertIn('intent.setPackage("org.fdroid.fdroid")', engine)
        self.assertNotIn("PackageInstaller.Session", src + engine)
        self.assertNotIn("ACTION_INSTALL_PACKAGE", src + engine)


if __name__ == "__main__":
    unittest.main()
