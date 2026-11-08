import pathlib
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]

class AndroidVersionSmokePolicyTests(unittest.TestCase):
    def test_expected_real_preview_base(self):
        text=(ROOT/"android/app/build.gradle").read_text()
        self.assertEqual(text.count("versionCode 1"),1)
        self.assertEqual(text.count("versionName '0.1.0-preview'"),1)

    def test_post_upgrade_ui_restarts_and_checks_both_current_snapshots(self):
        text=(ROOT/"scripts/android_two_version_smoke.sh").read_text()
        self.assertIn("adb shell wm dismiss-keyguard",text)
        self.assertIn("adb shell am force-stop ir.hamapp.store",text)
        self.assertIn('rm -f "$out/ui.xml" "$out/scrolled.xml"',text)
        self.assertIn('check_android_emulator_ui.py "$out/ui.xml" "$out/scrolled.xml"',text)
        self.assertIn('if [[ "$accepted" -ne 1 ]]',text)
        self.assertIn("ACTUAL_UPGRADED_UI_VALIDATION_FAILED",text)
        self.assertNotIn("ACTUAL_UPGRADED_UI_VALIDATION_SKIPPED",text)

    def test_real_upgrade_and_default_downgrade_guards_present(self):
        text=(ROOT/"scripts/android_two_version_smoke.sh").read_text()
        self.assertIn("adb install -r",text)
        self.assertIn("INSTALL_FAILED_VERSION_DOWNGRADE",text)
        self.assertIn("check_android_emulator_ui.py",text)
        self.assertNotIn("adb install -d ",text)
        self.assertNotIn("adb root",text)
        self.assertIn("INSTALL_FAILED_UPDATE_INCOMPATIBLE", text)
        self.assertIn("v2-foreign-signer.apk", text)
        self.assertIn("v2-truncated.apk", text)
        self.assertIn("corrupt_package_update_rejected", text)
        self.assertIn("installed_v2_preserved_after_denials", text)

if __name__=="__main__":
    unittest.main()
