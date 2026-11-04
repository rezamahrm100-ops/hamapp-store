"""Regression guards for separate third-party catalogue mode (not owned releases)."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
JAVA = ROOT / "android/app/src/main/java/ir/hamapp/store"
WEB = ROOT / "web"


class PublicUpstreamModeTests(unittest.TestCase):
    def test_fdroid_public_explorer_stays_explicit_and_external(self):
        engine = (JAVA / "FdroidEngine.java").read_text("utf-8")
        main = (JAVA / "MainActivity.java").read_text("utf-8")
        self.assertIn("FdroidEngine.requestPublicCatalog(this)", main)
        self.assertIn("getLaunchIntentForPackage(\"org.fdroid.fdroid\")", engine)
        self.assertIn("https://f-droid.org/", engine)
        self.assertIn(".setNegativeButton(\"لغو\", null)", engine)
        self.assertIn('activity.startActivity(launch)', engine)
        self.assertIn("requestOpen(Activity activity, JSONObject reviewedRepository)", engine)
        self.assertIn("signedRepositoryUri(", engine)
        self.assertNotIn("PackageInstaller.Session", engine + main)
        self.assertNotIn("ACTION_INSTALL_PACKAGE", engine + main)

    def test_no_new_android_install_permission_or_network_permission(self):
        manifest = (ROOT / "android/app/src/main/AndroidManifest.xml").read_text("utf-8")
        self.assertIn('<package android:name="org.fdroid.fdroid"/>', manifest)
        self.assertNotIn("QUERY_ALL_PACKAGES", manifest)
        self.assertNotIn("REQUEST_INSTALL_PACKAGES", manifest)
        self.assertNotIn("android.permission.INTERNET", manifest)
        self.assertNotIn("android.permission.QUERY_ALL_PACKAGES", manifest)

    def test_own_planned_app_install_remains_disabled(self):
        src = (JAVA / "MainActivity.java").read_text("utf-8")
        self.assertIn('action.setEnabled(approved)', src)
        self.assertIn('app.optString("status").equals("available") && repo != null', src)
        self.assertIn("F-Droid مستقل از این برنامه است.", src)

    def test_web_public_links_are_explicit_and_disjoint_from_owned_release(self):
        index = (WEB / "index.html").read_text("utf-8")
        js = (WEB / "app.js").read_text("utf-8")
        self.assertIn('href="https://f-droid.org/"', index)
        self.assertIn('href="https://learn.microsoft.com/en-us/windows/package-manager/winget/"', index)
        self.assertIn('rel="noopener noreferrer"', index)
        self.assertIn("app.status === 'released' && validUrl(app.download_url)", js)
        self.assertIn('فهرست اختصاصی هَماپ هنوز', index)

    def test_windows_explorer_is_separate_from_owner_reviewed_manager(self):
        ui = (ROOT / "windows_client/gui.py").read_text("utf-8")
        explorer = (ROOT / "windows_client/winget_explorer_ui.py").read_text("utf-8")
        self.assertIn("open_explorer(root)", ui)
        self.assertIn("execute_external(identity, operation)", explorer)
        self.assertIn('messagebox.askyesno(', explorer)
        self.assertIn("منبع ثالث", explorer)
        self.assertNotIn("shell=True", explorer)


if __name__ == "__main__":
    unittest.main()
