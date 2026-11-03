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

    def test_actual_filter_tutorial_on_truncated_repo_preview_is_dismissible(self):
        # Real emulator #41689898350 shows a truncated "Disposa...st only"
        # top bar and Filter/Got it popup, not a visible full repository name.
        actual = (
            '<node package="org.fdroid.fdroid" text="Disposa...st only"/>'
            '<node package="org.fdroid.fdroid" text="Filter"/>'
            '<node package="org.fdroid.fdroid" text="Got it" clickable="true" '
            'bounds="[216,219][294,266]"/>'
        )
        self.assertEqual(self.choice(actual, "dismiss-repo-hint"), (255, 242))
        self.assertIsNone(self.choice(actual.replace('text="Filter"',
                                                     'text="Other warning"'), "dismiss-repo-hint"))
        self.assertIsNone(self.choice(actual.replace('text="Got it"',
                                                     'text="Grant permission"'), "dismiss-repo-hint"))
        self.assertIsNone(self.choice(actual.replace("org.fdroid.fdroid",
                                                     "com.android.settings"), "dismiss-repo-hint"))
        self.assertIsNone(self.choice(actual.replace("[216,219][294,266]",
                                                     "[0,0][420,800]"), "dismiss-repo-hint"))
        first_repo_visit = actual.replace('text="Filter"', 'text="Repository list"')
        self.assertEqual(self.choice(first_repo_visit, "dismiss-repo-hint"), (255, 242))
        self.assertIsNone(self.choice(first_repo_visit.replace("Repository list", "Unknown"),
                                      "dismiss-repo-hint"))
        details_hint = actual.replace('text="Filter"', 'text="Repository"') + (
            '<node package="org.fdroid.fdroid" '
            'text="A repository is a source of apps. Mirrors are used to distribute the load."/>')
        self.assertEqual(self.choice(details_hint, "dismiss-repo-hint"), (255, 242))
        self.assertIsNone(self.choice(
            details_hint.replace("A repository is a source of apps.", "Grant system permissions."),
            "dismiss-repo-hint"))

    def test_real_f_droid_metered_repo_download_dialog_only(self):
        actual = (
            '<hierarchy><node package="org.fdroid.fdroid" '
            'text="Continue with mobile data?"/>'
            '<node package="org.fdroid.fdroid" text="Download" '
            'clickable="true" bounds="[185,390][290,438]"/></hierarchy>'
        )
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "real.xml"
            def show(xml):
                path.write_text(xml, encoding="utf-8")
                return path
            with patch.object(ui, "dump", side_effect=lambda dest: show(actual)), \
                 patch.object(ui, "adb") as adb, \
                 patch.object(ui.time, "sleep"):
                self.assertTrue(ui.confirm_visible_repo_download_dialog(path))
                adb.assert_called_once_with("shell", "input", "tap", "237", "414")
            for bad in (
                actual.replace("Continue with mobile data?", "Grant install permissions?"),
                actual.replace("org.fdroid.fdroid", "com.android.settings"),
            ):
                with patch.object(ui, "dump", side_effect=lambda dest: show(bad)), \
                     patch.object(ui, "adb") as adb, \
                     patch.object(ui.time, "sleep"):
                    self.assertFalse(ui.confirm_visible_repo_download_dialog(path))
                    adb.assert_not_called()
            with patch.object(ui, "dump", side_effect=lambda dest: show(
                    actual.replace('clickable="true"', 'clickable="false"'))), \
                 patch.object(ui, "adb") as adb, \
                 patch.object(ui.time, "sleep"):
                with self.assertRaisesRegex(RuntimeError, "metered"):
                    ui.confirm_visible_repo_download_dialog(path)
                adb.assert_not_called()

    def test_reject_unknown_actions_and_no_host_permission(self):
        with self.assertRaisesRegex(ValueError, "unknown"):
            self.choice("", "grant-anything")
        with patch.dict(ui.os.environ, {"GITHUB_ACTIONS": "false"}):
            with self.assertRaisesRegex(RuntimeError, "isolated"):
                ui.run()

    def test_navigation_failure_receipt_has_only_test_screen_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ui.xml"
            path.write_text(
                '<hierarchy><node package="org.fdroid.fdroid" text="F-Droid"/>'
                '<node package="org.fdroid.fdroid" text="Repositories"/>'
                '<node package="com.android.settings" text="Password: secret"/></hierarchy>',
                encoding="utf-8")
            signals = ui.screen_signals(path)
            self.assertTrue(signals["official_fdroid_title_visible"])
            self.assertTrue(signals["repositories_label_visible"])
            self.assertFalse(signals["disposable_repository_label_visible"])
            self.assertTrue(all(isinstance(x, bool) for x in signals.values()))
            self.assertEqual(len(signals), 10)
            self.assertFalse(signals["filter_tutorial_visible"])
            self.assertFalse(signals["repo_list_tutorial_visible"])
            self.assertFalse(signals["repo_details_tutorial_visible"])
            self.assertNotIn("Password", str(signals))
            self.assertNotIn("secret", str(signals))

    def test_no_client_database_or_installer_shortcuts(self):
        src = (ROOT / "scripts/fdroid_official_repo_refresh_ui.py").read_text("utf-8")
        self.assertIn("REAL_OFFICIAL_FDROID_REPO_DETAIL_FORCE_UPDATE_BUTTON_TAPPED", src)
        self.assertIn('actions = ("dismiss-repo-hint", "force-update"', src)
        self.assertIn("check for updates", src)
        self.assertIn("test-repository", src)
        # Actual F-Droid back stack may land directly in native RepoDetails.
        # Acceptance must depend on the exact repo UI, not an artificial route.
        self.assertIn('latest_signals["disposable_repository_label_visible"]', src)
        self.assertIn('latest_signals["native_check_for_updates_visible"]', src)
        self.assertNotIn('repository update did not follow genuine navigation', src)
        for forbidden in ('"adb", "install"', 'appops', "settings put",
                          'pm install', 'sqlite3', 'WRITE_SECURE_SETTINGS'):
            if forbidden in ("sqlite3", 'WRITE_SECURE_SETTINGS'):
                self.assertNotIn(forbidden, src)


if __name__ == "__main__":
    unittest.main()
