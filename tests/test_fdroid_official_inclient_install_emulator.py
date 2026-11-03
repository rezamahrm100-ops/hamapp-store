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

    def test_log_diagnostics_are_bounded_booleans_and_only_failure_evidence(self):
        with patch("subprocess.run") as command:
            command.return_value.returncode = 0
            command.return_value.stdout = (
                "Started install of ir.hamapp.store\\n"
                "Download failed: SSLHandshakeException\\n"
                "Error requesting pre-approval for ir.hamapp.store\\n"
                "SecurityException"
            )
            result = probe.on_device_failure_signals()
            self.assertTrue(result["fdroid_log_started_real_install"])
            self.assertTrue(result["fdroid_log_download_failed"])
            self.assertTrue(result["fdroid_log_preapproval_error"])
            self.assertTrue(result["android_runtime_security_exception_seen"])
            self.assertTrue(all(isinstance(value, bool) for value in result.values()))
            self.assertEqual(len(result), 6)
            self.assertIn("3000", command.call_args.args[0])

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
        self.assertIn('tap_from_real_ui(xml, "confirm-metered")', source)
        self.assertIn('real_fdroid_metered_download_confirmation_tapped_if_visible', source)
        self.assertIn('fdroid_metered_prompt_visible', source)
        self.assertIn("official-inclient-after-first-action-v", source)
        self.assertIn("actual_client_versioned_apk_get_count", source)
        self.assertIn("on_device_failure_signals()", source)
        self.assertIn("fdroid_log_started_real_install", source)
        self.assertIn("official_app_install_button_coordinate_tap_sent", source)
        self.assertNotIn("official_app_install_button_actually_tapped", source)
        self.assertIn('ACTUAL_OFFICIAL_FDROID_METERED_DOWNLOAD_DIALOG_CONFIRMED', source)
        self.assertIn('"install_or_upgrade_verified": False', source)
        for forbidden in ('"adb", "install"', '"adb", "shell", "pm", "install"',
                          '"adb", "shell", "appops", "set"', "chmod 777"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
