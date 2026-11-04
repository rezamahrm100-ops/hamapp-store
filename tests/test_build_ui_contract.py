"""Contract tests: approved action flags must derive from trusted builder gates."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_ui_contract


class UIBackendContractTests(unittest.TestCase):
    def setUp(self):
        self.sources = build_ui_contract.read_sources(ROOT)

    def test_public_preview_is_disabled_across_engines(self):
        payload = build_ui_contract.build(self.sources)
        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["contract"], "hamapp-ui-backend-v1")
        self.assertEqual({item["id"] for item in payload["apps"]},
                         {item["id"] for item in self.sources["apps"]["apps"]})
        self.assertTrue(all(not action["enabled"]
                            for app in payload["apps"]
                            for action in app["platforms"].values()))
        self.assertEqual(payload["engines"]["windows"]["approved_packages"], 0)
        self.assertFalse(payload["engines"]["android"]["repository_configured"])

    def test_build_is_deterministic_and_non_mutating(self):
        before = copy.deepcopy(self.sources)
        first = build_ui_contract.dumps(build_ui_contract.build(self.sources))
        second = build_ui_contract.dumps(build_ui_contract.build(self.sources))
        self.assertEqual(first, second)
        self.assertEqual(before, self.sources)
        self.assertEqual(
            json.loads(first)["catalog_sha256"],
            hashlib.sha256(json.dumps(
                self.sources["apps"], sort_keys=True, ensure_ascii=False,
                separators=(",", ":")).encode("utf-8")).hexdigest()
        )

    def test_unapproved_repo_metadata_never_enables_planned_app(self):
        data = copy.deepcopy(self.sources)
        data["android_repository"] = {
            "schema_version": 1, "repository": {
                "url": "https://example.org/fdroid/repo/",
                "fingerprint": "A" * 64,
            }
        }
        payload = build_ui_contract.build(data)
        self.assertTrue(payload["engines"]["android"]["repository_configured"])
        self.assertFalse(next(app for app in payload["apps"]
                              if "android" in app["platforms"])["platforms"]["android"]["enabled"])

    def test_unreviewed_winget_map_rejected(self):
        data = copy.deepcopy(self.sources)
        data["winget_packages"]["packages"] = [{
            "app_id": "windows-soon", "winget_id": "Vendor.Test",
            "version": "1.2.3", "artifact_sha256": "f" * 64,
        }]
        with self.assertRaises(ValueError):
            build_ui_contract.build(data)

    def test_malformed_repo_rejected(self):
        data = copy.deepcopy(self.sources)
        data["android_repository"] = {
            "schema_version": 1, "repository": {
                "url": "http://example.org/fdroid/repo/",
                "fingerprint": "A" * 64,
            }
        }
        with self.assertRaises(ValueError):
            build_ui_contract.build(data)

    def test_planned_app_with_binary_is_rejected(self):
        data = copy.deepcopy(self.sources)
        data["apps"]["apps"][0]["download_url"] = "https://example.org/fake.apk"
        with self.assertRaises(ValueError):
            build_ui_contract.build(data)

    def test_missing_source_or_injected_engine_rejected(self):
        data = copy.deepcopy(self.sources)
        del data["release_history"]
        with self.assertRaises(ValueError):
            build_ui_contract.build(data)
        data = copy.deepcopy(self.sources)
        data["unknown"] = {}
        with self.assertRaises(ValueError):
            build_ui_contract.build(data)

    def test_platform_actions_are_distinct_and_non_executable(self):
        payload = build_ui_contract.build(self.sources)
        for item in payload["apps"]:
            for name, action in item["platforms"].items():
                self.assertTrue(action["requires_user_consent"])
                self.assertNotIn("command", action)
                self.assertNotIn("installed", action)
                self.assertEqual(action["enabled"], False)
                self.assertEqual(
                    action["backend"],
                    {"android": "official-fdroid-companion",
                     "windows": "microsoft-winget",
                     "web": "verified-https-origin"}[name],
                )


if __name__ == "__main__":
    unittest.main()
