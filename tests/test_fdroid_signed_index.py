import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("verify_fdroid_signed_index", ROOT / "scripts/verify_fdroid_signed_index.py")
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)


class FdroidSignedIndexPreflightTests(unittest.TestCase):
    def setUp(self):
        self.config = {"schema_version": 1, "repository": {
            "url": "https://fdroid.repo.example.org/fdroid/repo/",
            "fingerprint": "a" * 64,
        }}
        self.expected_url = self.config["repository"]["url"]
        self.fp = "A" * 64

    def signed(self, url, verify_fingerprint=False, timeout=None):
        if url != self.expected_url + "?fingerprint=" + self.fp or not verify_fingerprint or timeout != 60:
            raise AssertionError("must require exact certificate fingerprint and index-verification mode")
        return ({"repo": {}, "packages": {}}, "etag")

    def test_official_downloader_receipt_cannot_approve_release(self):
        receipt = v.verify_signed_index(self.config, self.expected_url, self.fp, downloader=self.signed)
        self.assertTrue(receipt["index_v2_verified_with_pinned_key"])
        self.assertFalse(receipt["owner_publishing_approved"])
        self.assertFalse(receipt["private_signing_key_managed"])
        self.assertFalse(receipt["live_apk_install_update_verified"])
        self.assertFalse(receipt["production_store_ready"])

    def test_repo_config_defaults_null_and_fails_closed(self):
        config = json.loads((ROOT / "catalog/android_repository.json").read_text(encoding="utf-8"))
        with self.assertRaises(v.SignedIndexError):
            v.verify_signed_index(config, self.expected_url, self.fp, downloader=self.signed)

    def test_wrong_independent_pinned_url_rejected(self):
        with self.assertRaisesRegex(v.SignedIndexError, "origin"):
            v.verify_signed_index(self.config, "https://other.example.org/fdroid/repo/", self.fp, downloader=self.signed)

    def test_wrong_independent_fingerprint_rejected(self):
        with self.assertRaisesRegex(v.SignedIndexError, "signing key"):
            v.verify_signed_index(self.config, self.expected_url, "b" * 64, downloader=self.signed)

    def test_unsigned_index_download_fails(self):
        def refuse(url, verify_fingerprint=True, timeout=60):
            raise RuntimeError("bad signature")
        with self.assertRaises(v.SignedIndexError):
            v.verify_signed_index(self.config, self.expected_url, self.fp, downloader=refuse)

    def test_upstream_response_without_signed_index_fails(self):
        for bad in (None, {}, (None, None), ({"repo": {}}, None), ({"packages": {}}, None),
                    ({"repo": {}, "packages": []}, None)):
            with self.subTest(bad=bad), self.assertRaises(v.SignedIndexError):
                v.verify_signed_index(self.config, self.expected_url, self.fp, downloader=lambda *args, **kwargs: bad)

    def test_no_unsigned_fallback(self):
        def downloader(url, verify_fingerprint=False, timeout=60):
            if not verify_fingerprint:
                raise AssertionError("signature verification bypass attempted")
            return {"repo": {}, "packages": {}}, None
        self.assertEqual(v.verify_signed_index(self.config, self.expected_url, self.fp,
                                               downloader=downloader)["package_count"], 0)

    def test_localhost_rejected(self):
        for host in ("repo.localhost", "repo.internal", "localhost.local", "127.0.0.1"):
            with self.subTest(host=host):
                self.config["repository"]["url"] = "https://" + host + "/fdroid/repo/"
                with self.assertRaises(v.SignedIndexError):
                    v.verify_signed_index(self.config, self.config["repository"]["url"], self.fp, downloader=self.signed)

    def test_repo_key_does_not_equal_production_key(self):
        result = v.verify_signed_index(self.config, self.expected_url, self.fp, downloader=self.signed)
        self.assertNotIn("private_key", result)
        self.assertNotIn("keystore", result)

    def test_hosted_unapproved_repo_refused(self):
        self.config["repository"]["url"] = "https://github.com/fdroid/repo/"
        with self.assertRaises(v.SignedIndexError):
            v.verify_signed_index(self.config, self.config["repository"]["url"], self.fp, downloader=self.signed)


if __name__ == "__main__":
    unittest.main()
