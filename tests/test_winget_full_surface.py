"""One native WinGet engine interface, all documented command families.

No arbitrary process execution, shell text, unchecked silent installs or
cross-source trust promotion. The standard package explorer retains its more
restrictive exact-ID install/update/uninstall path.
"""
import sys
import unittest
from unittest.mock import patch, Mock
from types import SimpleNamespace

from windows_client import winget_full_surface as engine


class FullWinGetEngineTests(unittest.TestCase):
    def test_all_documented_engine_families_have_one_adapter(self):
        required = {"source", "search", "show", "list", "features", "settings",
                    "export", "import", "hash", "validate", "pin", "configure",
                    "download", "repair", "dscv3"}
        self.assertTrue(required.issubset(engine.OPERATIONS))
        self.assertTrue(engine.MANAGED_SEPARATELY.issubset(
            {"install", "upgrade", "uninstall"}))

    def test_mutable_source_and_configuration_require_consent(self):
        for verb, arg in [("source", "add --name custom"), ("pin", "add --id Example.App"),
                          ("import", "--import-file list.json"),
                          ("configure", "--file package.yaml"),
                          ("repair", "--id Example.App"), ("dscv3", "resource list")]:
            with self.subTest(verb=verb):
                operation = engine.plan(verb, arg)
                self.assertTrue(operation.state_changing)
                with patch.object(engine.sys, "platform", "win32"):
                    with self.assertRaises(engine.EngineError):
                        engine.execute(operation)

    def test_safe_query_and_official_engine_args(self):
        for verb, arg in [("--info", ""), ("--help", ""), ("source", "list"),
                          ("source", "export"), ("pin", "list"),
                          ("show", "--id Example.App"), ("features", ""),
                          ("settings", "export")]:
            with self.subTest(verb=verb):
                spec = engine.plan(verb, arg)
                self.assertFalse(spec.state_changing)
                fake = Mock(return_value=SimpleNamespace(returncode=0,
                                                         stdout="real CLI output", stderr=""))
                with patch.object(engine.sys, "platform", "win32"):
                    receipt = engine.execute(spec, runner=fake)
                args, kwargs = fake.call_args
                self.assertEqual(args[0][0], "winget")
                self.assertFalse(kwargs["shell"])
                self.assertTrue(receipt["official_cli_exit_success"])
                self.assertFalse(receipt["owner_publisher_verified"])

    def test_unsafe_alias_or_bypass_options_are_denied(self):
        for verb, text in [
            ("install", "--id Example.App"), ("upgrade", "--all"),
            ("uninstall", "--id Example.App"),
            ("source", "add --name x --accept-source-agreements"),
            ("configure", "--file x.yaml --force"),
            ("download", "--id x --ignore-security-hash"),
            ("dscv3", "list & powershell.exe"),
            ("export", "--output z\ncommand"),
            ("source", "remove --header BearerXYZ"),
            ("list", "--proxy http://example.invalid")]:
            with self.subTest(verb=verb, args=text), self.assertRaises(engine.EngineError):
                engine.plan(verb, text)

    def test_unchecked_dataclass_must_not_bypass_mutation_guard(self):
        fake = Mock()
        forged = engine.Plan("source", ("add", "--name", "X"), False, False)
        with patch.object(engine.sys, "platform", "win32"):
            with self.assertRaises(engine.EngineError):
                engine.execute(forged, runner=fake, allow_mutation=True)
        fake.assert_not_called()

    def test_explicit_mutation_only_exact_typed_win_get_binary(self):
        spec = engine.plan("source", "update")
        self.assertTrue(spec.state_changing)
        runner = Mock(return_value=SimpleNamespace(returncode=0, stdout="Updated", stderr=""))
        with patch.object(engine.sys, "platform", "win32"):
            answer = engine.execute(spec, runner=runner, allow_mutation=True)
        self.assertEqual(runner.call_args.args[0], ["winget", "source", "update"])
        self.assertTrue(answer["state_change_requested"])
        self.assertFalse(answer["installed_version_independently_verified"])

    def test_native_ui_discoverable_without_new_external_store(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        explorer = (root / "windows_client/winget_explorer_ui.py").read_text("utf-8")
        ui = (root / "windows_client/winget_full_ui.py").read_text("utf-8")
        self.assertIn("open_full_surface(window)", explorer)
        self.assertIn("engine.plan(", ui)
        self.assertIn("engine.execute(", ui)
        self.assertIn("messagebox.askyesno", ui)
        self.assertNotIn("shell=True", explorer + ui)


if __name__ == "__main__":
    unittest.main()
