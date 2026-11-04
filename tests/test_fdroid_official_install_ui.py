"""Fail-closed accessible controls for real F-Droid in-client lifecycle QA."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import fdroid_official_install_ui as ui


class OfficialInClientInstallUiTests(unittest.TestCase):
    def choose(self, raw, action):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "window.xml"
            path.write_text("<hierarchy>" + raw + "</hierarchy>", encoding="utf-8")
            return ui.select(path, action)

    def test_exact_official_app_install_clickable_parent(self):
        raw = (
            '<node package="org.fdroid.fdroid" text="هَماپ" clickable="false" '
            'bounds="[20,40][230,80]"/>'
            '<node package="org.fdroid.fdroid" clickable="true" bounds="[60,180][268,228]">'
            '<node package="org.fdroid.fdroid" text="Install" clickable="false" '
            'bounds="[93,187][225,220]"/></node>'
        )
        self.assertEqual(self.choose(raw, "install"), (164, 204))
        self.assertIsNone(self.choose(raw, "update"))

    def test_actual_f_droid_update_requires_target_app_visible(self):
        raw = (
            '<node package="org.fdroid.fdroid" text="HamApp" clickable="false"/>'
            '<node package="org.fdroid.fdroid" text="Update" clickable="true" '
            'bounds="[70,250][280,295]"/>'
        )
        self.assertEqual(self.choose(raw, "update"), (175, 272))
        self.assertIsNone(self.choose(raw.replace("HamApp", "Unrelated App"), "update"))

    def test_never_click_system_permission_or_other_package_as_f_droid_control(self):
        raw = (
            '<node package="com.google.android.permissioncontroller" text="هَماپ"/>'
            '<node package="com.google.android.permissioncontroller" text="Install" clickable="true" '
            'bounds="[70,250][280,295]"/>'
        )
        self.assertIsNone(self.choose(raw, "install"))
        self.assertEqual(self.choose(raw, "confirm-installer"), (175, 272))

    def test_system_installer_requires_target_app_and_real_package(self):
        raw = (
            '<node package="com.android.packageinstaller" text="هماپ"/>'
            '<node package="com.android.packageinstaller" text="Install" clickable="true" '
            'bounds="[100,400][250,453]"/>'
        )
        self.assertEqual(self.choose(raw, "confirm-installer"), (175, 426))
        self.assertIsNone(self.choose(raw.replace("هماپ", "Other app"), "confirm-installer"))
        self.assertIsNone(self.choose(raw.replace("com.android.packageinstaller",
                                                   "com.android.settings"), "confirm-installer"))

    def test_dismiss_only_actual_fdroid_tutorial_with_bounded_control(self):
        good = '<node package="org.fdroid.fdroid" text="Got it" clickable="true" bounds="[160,180][280,224]"/>'
        self.assertEqual(self.choose(good, "dismiss-hint"), (220, 202))
        self.assertIsNone(self.choose(good.replace('package="org.fdroid.fdroid"',
                                                    'package="com.android.settings"'), "dismiss-hint"))
        self.assertIsNone(self.choose(good.replace("[160,180][280,224]",
                                                    "[0,0][400,800]"), "dismiss-hint"))

    def test_real_f_droid_metered_download_confirmation_requires_exact_dialog(self):
        # Upstream MeteredConnectionDialog titles its confirmation action
        # "Download"; without the exact title it MUST NOT tap a random button.
        prompt = (
            '<node package="org.fdroid.fdroid" text="Continue with mobile data?" '
            'clickable="false"/>'
            '<node package="org.fdroid.fdroid" text="Download" clickable="true" '
            'bounds="[160,400][300,449]"/>'
        )
        self.assertEqual(self.choose(prompt, "confirm-metered"), (230, 424))
        self.assertIsNone(self.choose(prompt.replace("Continue with mobile data?",
                                                      "Permission required"), "confirm-metered"))
        self.assertIsNone(self.choose(prompt.replace("org.fdroid.fdroid",
                                                     "com.android.settings"), "confirm-metered"))
        self.assertIsNone(self.choose(prompt.replace("[160,400][300,449]",
                                                     "[0,0][400,800]"), "confirm-metered"))
        self.assertIsNone(self.choose(prompt.replace("Download", "Install"),
                                      "confirm-metered"))

    def test_real_android_unknown_source_dialog_settings_requires_fdroid_security_context(self):
        prompt = (
            '<node package="com.google.android.packageinstaller" text="F-Droid" '
            'clickable="false"/>'
            '<node package="com.google.android.packageinstaller" '
            'text="For your security, your phone currently is not allowed to install unknown apps from this source."/>'
            '<node package="com.google.android.packageinstaller" text="Settings" '
            'clickable="true" bounds="[216,380][304,429]"/>'
        )
        self.assertEqual(self.choose(prompt, "open-source-settings"), (260, 404))
        self.assertIsNone(self.choose(prompt.replace("F-Droid", "Other App"),
                                      "open-source-settings"))
        self.assertIsNone(self.choose(prompt.replace("unknown apps from this source",
                                                      "notification permission"),
                                      "open-source-settings"))
        self.assertIsNone(self.choose(prompt.replace("com.google.android.packageinstaller",
                                                      "com.android.settings"),
                                      "open-source-settings"))
        self.assertIsNone(self.choose(prompt.replace("[216,380][304,429]",
                                                      "[0,0][400,800]"),
                                      "open-source-settings"))

    def test_real_android_fdroid_unknown_source_switch_state_and_safe_toggle(self):
        content = (
            '<node package="com.android.settings" text="Install unknown apps"/>'
            '<node package="com.android.settings" text="F-Droid"/>'
            '<node package="com.android.settings" text="Allow from this source"/>'
            '<node package="com.android.settings" class="android.widget.Switch" '
            'clickable="true" checked="false" enabled="true" '
            'bounds="[238,205][292,249]"/>'
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.xml"
            path.write_text("<hierarchy>" + content + "</hierarchy>", encoding="utf-8")
            self.assertIs(ui.source_settings_state(path), False)
            self.assertEqual(ui.select(path, "allow-source-settings"), (265, 227))
            path.write_text("<hierarchy>" + content.replace('checked="false"',
                                                               'checked="true"') +
                            "</hierarchy>", encoding="utf-8")
            self.assertIs(ui.source_settings_state(path), True)
            self.assertIsNone(ui.select(path, "allow-source-settings"))
            for changed in (
                content.replace("F-Droid", "Unknown App"),
                content.replace("Allow from this source", "Allow all access"),
                content.replace("com.android.settings", "com.android.permissioncontroller"),
                content.replace('enabled="true"', 'enabled="false"'),
                content.replace('class="android.widget.Switch"', 'class="android.widget.Button"'),
            ):
                with self.subTest(changed=changed[:80]):
                    path.write_text("<hierarchy>" + changed + "</hierarchy>", encoding="utf-8")
                    self.assertIsNone(ui.source_settings_state(path))
                    self.assertIsNone(ui.select(path, "allow-source-settings"))

    def test_invalid_bounds_or_wrong_label_rejected(self):
        raw = (
            '<node package="org.fdroid.fdroid" text="هَماپ"/>'
            '<node package="org.fdroid.fdroid" text="Install" clickable="true" '
            'bounds="[200,180][10,220]"/>'
        )
        self.assertIsNone(self.choose(raw, "install"))
        self.assertIsNone(self.choose(raw.replace("Install", "Install unrelated"), "install"))


if __name__ == "__main__":
    unittest.main()
