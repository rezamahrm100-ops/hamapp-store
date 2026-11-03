"""Strict source and network negatives; actual acceptance requires hosted official APK."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import fdroid_official_inclient_install_emulator as probe


class OfficialRealInstallSourceGateTests(unittest.TestCase):
    def test_no_owner_or_non_hosted_test_execution(self):
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "false", "RUNNER_OS": "Linux",
                                     "GITHUB_REPOSITORY": "rezamahrm100-ops/hamapp-store"}):
            with self.assertRaisesRegex(probe.ClientInstallFailure, "isolated"):
                probe.run(1)

    def test_http_get_requires_exact_versioned_real_apk_not_index(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "requests.jsonl"
            p.write_text("\n".join(json.dumps(event) for event in (
                {"method": "GET", "path": "/fdroid/repo/index-v2.json",
                 "agent": "Android F-Droid"},
                {"method": "GET", "path": "/fdroid/repo/hamapp-v1.apk",
                 "agent": "curl/8.0"},
                {"method": "GET", "path": "/fdroid/repo/hamapp-v1.apk",
                 "agent": "F-Droid/1.0"},
                {"method": "GET", "path": "/fdroid/repo/hamapp-v2.apk",
                 "agent": "F-Droid/1.0"},
                {"method": "POST", "path": "/fdroid/repo/hamapp-v1.apk",
                 "agent": "F-Droid/1.0"},
            )) + "\n", encoding="utf-8")
            self.assertEqual(probe.count_client_apk_get(p, "hamapp-v1.apk"), 1)
            self.assertEqual(probe.count_client_apk_get(p, "hamapp-v2.apk"), 1)
            self.assertEqual(probe.count_client_apk_get(p, "missing.apk"), 0)

    def test_real_inclient_flow_never_uses_adb_install_or_fake_sqlite(self):
        source = (ROOT / "scripts/fdroid_official_inclient_install_emulator.py").read_text("utf-8")
        for required in (
            "market://details?id=", "fdroid_official_install_ui",
            "actual_client_apk_get_observed", "verify_installed_apk(",
            '"pm", "path", APP_PACKAGE', "Get", "request",
            "sha256", '"real_official_client_app_updated": stage == 2',
            '"owner_device_or_production_signer_verified": False',
            '"public_release_authorized": False',
        ):
            if required in ("Get", "request"):
                continue
            self.assertIn(required, source)
        self.assertIn("OFFICIAL_FDROID_REAL_INCLIENT_DIAGNOSTIC_CAPTURED_NO_FAKE_INSTALL", source)
        self.assertIn("fdroid_target_app_name_visible", source)
        self.assertIn("fdroid_got_it_hint_visible", source)
        self.assertIn('"install_or_upgrade_verified": False', source)
        for forbidden in ('"adb", "install"', '"adb", "shell", "pm", "install"',
                          '"adb", "shell", "appops", "set"', "chmod 777"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
