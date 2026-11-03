"""Exact official F-Droid UI-only signed repository v2 refresh negatives."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import fdroid_official_repo_refresh_ui as ui


class RealRepoForceRefreshSelectorTests(unittest.TestCase):
    def choice(self, body, action):
        with tempfile.TemporaryDirectory() as tmp:
            xml = Path(tmp) / "live.xml"
            xml.write_text("<hierarchy>" + body + "</hierarchy>", encoding="utf-8")
            return ui.select(xml, action)

    def test_only_real_discover_repositories_navigation(self):
        body = (
            '<node package="org.fdroid.fdroid" text="F-Droid"/>'
            '<node package="org.fdroid.fdroid" content-desc="Repositories" clickable="true" '
            'bounds="[320,10][374,60]"/>'
        )
        self.assertEqual(self.choice(body, "repositories"), (347, 35))
        self.assertIsNone(self.choice(body.replace('text="F-Droid"',
                                                   'text="HamApp"'), "repositories"))
        self.assertIsNone(self.choice(body.replace("org.fdroid.fdroid",
                                                   "com.android.settings"), "repositories"))

    def test_repo_row_requires_exact_signed_test_repository_not_neighbor(self):
        body = (
            '<node package="org.fdroid.fdroid" text="Repositories"/>'
            '<node package="org.fdroid.fdroid" clickable="true" bounds="[10,75][385,148]">'
            '<node package="org.fdroid.fdroid" text="Disposable HamApp emulator install test only" '
            'clickable="false" bounds="[25,87][345,125]"/>'
            '</node>'
        )
        self.assertEqual(self.choice(body, "test-repository"), (197, 111))
        self.assertIsNone(self.choice(body.replace("Disposable HamApp emulator install test only",
                                                   "Unknown application repository"),
                                      "test-repository"))
        self.assertIsNone(self.choice(body.replace('text="Repositories"',
                                                   'text="Unknown"'), "test-repository"))
        self.assertIsNone(self.choice(body.replace("org.fdroid.fdroid",
                                                   "com.android.settings"), "test-repository"))

    def test_native_repo_details_exact_check_for_updates_button(self):
        body = (
            '<node package="org.fdroid.fdroid" text="Disposable HamApp emulator install test only"/>'
            '<node package="org.fdroid.fdroid" content-desc="Check for updates" clickable="true" '
            'bounds="[310,5][360,60]"/>'
        )
        self.assertEqual(self.choice(body, "force-update"), (335, 32))
        self.assertIsNone(self.choice(body.replace("Check for updates", "Refresh"),
                                      "force-update"))
        self.assertIsNone(self.choice(body.replace("Disposable HamApp emulator install test only",
                                                   "Other repository"), "force-update"))
        self.assertIsNone(self.choice(body.replace('clickable="true"',
                                                   'clickable="false"'), "force-update"))
        self.assertIsNone(self.choice(body.replace("[310,5][360,60]",
                                                   "[0,0][400,800]"), "force-update"))
        self.assertIsNone(self.choice(body.replace("org.fdroid.fdroid",
                                                   "com.android.permissioncontroller"), "force-update"))
        second = ('<node package="org.fdroid.fdroid" content-desc="Check for updates" '
                  'clickable="true" bounds="[245,5][300,60]"/>')
        self.assertIsNone(self.choice(body + second, "force-update"))

    def test_reject_unknown_actions_and_no_host_permission(self):
        with self.assertRaisesRegex(ValueError, "unknown"):
            self.choice("", "grant-anything")
        with patch.dict(ui.os.environ, {"GITHUB_ACTIONS": "false"}):
            with self.assertRaisesRegex(RuntimeError, "isolated"):
                ui.run()

    def test_no_client_database_or_installer_shortcuts(self):
        src = (ROOT / "scripts/fdroid_official_repo_refresh_ui.py").read_text("utf-8")
        self.assertIn("REAL_OFFICIAL_FDROID_REPO_DETAIL_FORCE_UPDATE_BUTTON_TAPPED", src)
        self.assertIn("check for updates", src)
        self.assertIn("test-repository", src)
        self.assertIn('"repositories" not in transitions', src)
        for forbidden in ('"adb", "install"', 'appops', "settings put",
                          'pm install', 'sqlite3', 'WRITE_SECURE_SETTINGS'):
            if forbidden in ("sqlite3", 'WRITE_SECURE_SETTINGS'):
                self.assertNotIn(forbidden, src)


if __name__ == "__main__":
    unittest.main()
