"""Design-system integration must not change application install boundaries."""
import re
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AtlasOpenSourceUIContract(unittest.TestCase):
    def test_android_pinned_native_material3_and_preserves_fdroid(self):
        gradle = (ROOT / "android/app/build.gradle").read_text("utf-8")
        theme = (ROOT / "android/app/src/main/res/values/styles.xml").read_text("utf-8")
        native = (ROOT / "android/app/src/main/java/ir/hamapp/store/MainActivity.java").read_text("utf-8")
        self.assertIn("com.google.android.material:material:1.14.0", gradle)
        self.assertIn('parent="Theme.Material3.Dark.NoActionBar"', theme)
        for material in ("MaterialButton", "TextInputLayout", "TextInputEditText"):
            self.assertIn(material, native)
        self.assertIn("action.setEnabled(approved)", native)
        self.assertIn('app.optString("status").equals("available") && repo != null', native)
        self.assertIn("FdroidEngine.requestOpen(this, repo)", native)
        self.assertIn("FdroidEngine.requestPublicCatalog(this)", native)
        self.assertNotIn("PackageInstaller.Session", native)

    def test_windows_real_ttkbootstrap_builds_and_safe_fallback(self):
        helper = (ROOT / "windows_client/ui_theme.py").read_text("utf-8")
        main = (ROOT / "windows_client/gui.py").read_text("utf-8")
        explorer = (ROOT / "windows_client/winget_explorer_ui.py").read_text("utf-8")
        for path in (ROOT / ".github/workflows/owner-installable-previews.yml",
                     ROOT / ".github/workflows/windows-client-preview.yml"):
            self.assertIn("ttkbootstrap==2.2.6", path.read_text("utf-8"))
        self.assertIn('ttkbootstrap.Style(theme="bootstrap-dark")', helper)
        self.assertIn('ttk.Style(root).theme_use("clam")', helper)
        self.assertIn("install_theme(root)", main)
        self.assertIn("ttk.Button", main)
        self.assertIn("ttk.Button", explorer)
        self.assertIn("messagebox.askyesno(", explorer)
        self.assertIn("execute_external(identity, operation)", explorer)
        self.assertNotIn("shell=True", main + explorer)

    def test_web_offline_tokens_and_RTL_are_self_contained(self):
        css = (ROOT / "web/styles.css").read_text("utf-8")
        sw = (ROOT / "web/sw.js").read_text("utf-8")
        page = (ROOT / "web/index.html").read_text("utf-8")
        self.assertIn('lang="fa" dir="rtl"', page)
        self.assertIn("--accent:#9fe3c7", css)
        self.assertIn("@media(prefers-reduced-motion:reduce)", css)
        self.assertIn("hamapp-shell-v4", sw)
        self.assertNotIn("https://cdn.", page)
        self.assertNotIn("document.write(", page)
        self.assertNotIn("installPackage(", page)
        self.assertIn('rel="stylesheet" href="./styles.css"', page)


if __name__ == "__main__":
    unittest.main()
