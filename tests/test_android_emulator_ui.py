import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("check_android_emulator_ui", ROOT / "scripts/check_android_emulator_ui.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class EmulatorUiParserTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.xml = Path(self.tmp.name) / "window.xml"

    def write(self, disabled=True, title=True, planned=True, public=True, public_enabled=True):
        content = [
            '<hierarchy rotation="0">',
            '<node text="' + ("هَماپ" if title else "other") + '" enabled="true"/>',
            '<node text="مدیریت در هَماپ" enabled="' + ("false" if disabled else "true") + '"/>',
            ('<node text="برنامه‌های عمومی" enabled="' + ("true" if public_enabled else "false") + '"/>') if public else "",
            '<node text="' + ("در دست توسعه" if planned else "آماده") + '" enabled="true"/>',
            '</hierarchy>',
        ]
        self.xml.write_text("".join(content), encoding="utf-8")

    def test_requires_safe_disabled_install(self):
        self.write()
        self.assertEqual(module.check_ui(self.xml), 1)

    def test_two_real_snapshots_do_not_count_the_public_action_twice(self):
        # Fixed header actions are present in both captures. Preserve the
        # requirement that public browsing is enabled and owner installs are
        # disabled; do not reject the same node simply for being seen twice.
        self.write()
        self.assertEqual(module.check_ui(self.xml, self.xml), 1)

    def test_rejects_enabled_install(self):
        self.write(disabled=False)
        with self.assertRaisesRegex(ValueError, "must be disabled"):
            module.check_ui(self.xml)

    def test_public_explorer_is_separate_and_must_be_enabled(self):
        self.write(public=False)
        with self.assertRaisesRegex(ValueError, "public F-Droid"):
            module.check_ui(self.xml)
        self.write(public_enabled=False)
        with self.assertRaisesRegex(ValueError, "public F-Droid"):
            module.check_ui(self.xml)

    def test_rejects_missing_title(self):
        self.write(title=False)
        with self.assertRaises(ValueError):
            module.check_ui(self.xml)

    def test_rejects_missing_planned_label(self):
        self.write(planned=False)
        with self.assertRaises(ValueError):
            module.check_ui(self.xml)

    def test_missing_file_fails(self):
        with self.assertRaises(OSError):
            module.check_ui(self.xml)


if __name__ == "__main__":
    unittest.main()
