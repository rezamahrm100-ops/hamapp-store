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
