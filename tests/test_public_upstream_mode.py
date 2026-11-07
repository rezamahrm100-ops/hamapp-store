"""Regression guards for separate third-party catalogue mode (not owned releases)."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
JAVA = ROOT / "android/app/src/main/java/ir/hamapp/store"
WEB = ROOT / "web"


class PublicUpstreamModeTests(unittest.TestCase):
    def test_embedded_upstream_repository_is_cryptographically_verified(self):
        engine = (JAVA / "InternalFdroidStore.java").read_text("utf-8")
        main = (JAVA / "MainActivity.java").read_text("utf-8")
        self.assertIn("org.fdroid.index.v2.EntryVerifier", engine)
        self.assertIn("https://f-droid.org/repo/", engine)
        self.assertIn("entry.jar", engine)
        self.assertIn("index-v2.json", engine)
        self.assertIn("shaFile(existing)", engine)
        self.assertIn("setInstanceFollowRedirects(false)", engine)
        self.assertIn("InternalFdroidStore.openPublic(this", main)
        self.assertNotIn("FdroidEngine", main)
        self.assertNotIn("PublicFdroidSearch", main)

    def test_internal_install_still_requires_android_user_consent_and_signer(self):
        install = (JAVA / "EmbeddedApkInstaller.java").read_text("utf-8")
        result = (JAVA / "InstallResultActivity.java").read_text("utf-8")
        manifest = (ROOT / "android/app/src/main/AndroidManifest.xml").read_text("utf-8")
        self.assertIn("PackageInstaller.Session", install)
        self.assertIn("canRequestPackageInstalls", install)
        self.assertIn("getApkContentsSigners", install)
        self.assertIn("STATUS_PENDING_USER_ACTION", result)
        self.assertIn("android.permission.REQUEST_INSTALL_PACKAGES", manifest)
        self.assertNotIn("QUERY_ALL_PACKAGES", manifest)
        self.assertNotIn("org.fdroid.fdroid", manifest)
        self.assertIn('android:exported="false"', manifest)

    def test_own_planned_app_install_remains_disabled(self):
        src = (JAVA / "MainActivity.java").read_text("utf-8")
        self.assertIn('action.setEnabled(approved)', src)
        self.assertIn('app.optString("status").equals("available") && repo != null', src)
        self.assertIn("فروشگاه عمومی متن‌باز از ناشران اختصاصی جداست.", src)

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
        self.assertIn("table.selection() != (identity,)", explorer)
        self.assertIn("selected_id = None", explorer)
        self.assertIn('messagebox.askyesno(', explorer)
        self.assertIn("منبع ثالث", explorer)
        self.assertNotIn("shell=True", explorer)


if __name__ == "__main__":
    unittest.main()
