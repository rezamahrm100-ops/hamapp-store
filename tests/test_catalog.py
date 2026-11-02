import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("validate_catalog", ROOT / "scripts/validate_catalog.py")
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.sample = {"schema_version": 1, "apps": [
            {"id": "demo", "name_fa": "نمونه", "name_en": "Demo", "description": "Test",
             "platforms": ["android"], "status": "planned", "version": None, "download_url": None}
        ]}
        self.pub = {"schema_version": 1, "publishers": [{
            "app_id": "demo", "source_repo": "demo-project", "platform": "android",
            "certificate_sha256": "b" * 64, "package_id": "ir.hamapp.demo"
        }]}
        self.history = {"schema_version": 1, "releases": [{
            "app_id": "demo", "platform": "android", "version": "1.0.0",
            "version_code": 7, "source_repo": "demo-project", "package_id": "ir.hamapp.demo",
            "certificate_sha256": "b" * 64, "artifact_sha256": "a" * 64,
            "status": "approved"
        }], "revoked_signers": []}

    def approved(self):
        app = self.sample["apps"][0]
        app.update(
            status="released", version="1.0.0",
            download_url="https://github.com/rezamahrm100-ops/demo-project/releases/download/v1.0.0/demo.apk",
            release_proof={
                "sha256": "a" * 64, "size_bytes": 100,
                "certificate_sha256": "b" * 64, "source_repo": "demo-project",
                "package_id": "ir.hamapp.demo", "version_code": 7
            }
        )
        return app

    def test_real_catalog(self):
        data = json.loads((ROOT / "catalog/apps.json").read_text(encoding="utf-8"))
        self.assertFalse(validator.validate(data))

    def test_planned_cannot_advertise_download(self):
        self.sample["apps"][0]["download_url"] = "https://example.com/not-built.apk"
        self.assertTrue(validator.validate(self.sample))

    def test_released_https_without_owner_approval_fails(self):
        self.sample["apps"][0].update(
            status="released", version="1.0.0", download_url="https://example.org/test.apk")
        self.assertTrue(validator.validate(self.sample))

    def test_http_rejected(self):
        app = self.approved()
        app["download_url"] = app["download_url"].replace("https:", "http:")
        self.assertTrue(validator.validate(self.sample, self.pub, self.history))

    def test_approved_fixture_passes_static_metadata_checks(self):
        self.approved()
        self.assertEqual(validator.validate(self.sample, self.pub, self.history), [])

    def test_approved_fixture_does_not_publish_on_disk(self):
        self.approved()
        self.assertFalse(validator.validate(self.sample, self.pub, self.history))
        self.assertTrue(all(a["status"] == "planned" for a in
                            json.loads((ROOT / "catalog/apps.json").read_text(encoding="utf-8"))["apps"]))

    def test_mismatched_digest_blocked(self):
        app = self.approved()
        app["release_proof"]["sha256"] = "c" * 64
        self.assertTrue(validator.validate(self.sample, self.pub, self.history))

    def test_mismatched_certificate_blocked(self):
        app = self.approved()
        app["release_proof"]["certificate_sha256"] = "c" * 64
        self.assertTrue(validator.validate(self.sample, self.pub, self.history))

    def test_wrong_source_link_blocked(self):
        app = self.approved()
        app["download_url"] = app["download_url"].replace("demo-project", "attacker")
        self.assertTrue(validator.validate(self.sample, self.pub, self.history))

    def test_revoked_certificate_blocked(self):
        self.approved()
        self.history["revoked_signers"].append("b" * 64)
        self.assertTrue(validator.validate(self.sample, self.pub, self.history))

    def test_revoked_latest_version_blocked(self):
        self.approved()
        self.history["releases"][0]["status"] = "revoked"
        self.assertTrue(validator.validate(self.sample, self.pub, self.history))

    def test_old_release_not_listed_if_newer_record_exists(self):
        self.approved()
        recent = dict(self.history["releases"][0])
        recent.update(version="2.0.0", version_code=8, artifact_sha256="c" * 64)
        self.history["releases"].append(recent)
        self.assertTrue(validator.validate(self.sample, self.pub, self.history))

    def test_no_history_no_download(self):
        self.approved()
        self.history["releases"] = []
        self.assertTrue(validator.validate(self.sample, self.pub, self.history))

    def test_changed_version_code_rejected(self):
        self.approved()["release_proof"]["version_code"] = 8
        self.assertTrue(validator.validate(self.sample, self.pub, self.history))

    def test_multiplatform_release_rejected(self):
        self.approved()["platforms"].append("windows")
        self.assertTrue(validator.validate(self.sample, self.pub, self.history))

    def test_web_release_requires_separate_policy(self):
        app = self.approved()
        app["platforms"] = ["web"]
        self.assertTrue(validator.validate(self.sample, self.pub, self.history))

    def test_changelog_requires_real_released_version(self):
        self.sample["apps"][0]["changelog"] = "New features"
        self.assertTrue(validator.validate(self.sample, self.pub, self.history))
        self.sample["apps"][0].pop("changelog")
        self.approved()["changelog"] = "Reviewed version notes"
        self.assertEqual(validator.validate(self.sample, self.pub, self.history), [])
        self.sample["apps"][0]["changelog"] = "a" * 2001
        self.assertTrue(validator.validate(self.sample, self.pub, self.history))

    def test_duplicate_id_rejected(self):
        self.sample["apps"].append(self.sample["apps"][0].copy())
        self.assertTrue(validator.validate(self.sample))

    def test_malformed_registry_fails_closed(self):
        self.approved()
        self.assertTrue(validator.validate(self.sample, {"schema_version": 1, "publishers": "not a list"}, self.history))


if __name__ == "__main__":
    unittest.main()
