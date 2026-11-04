"""Exact WinGet installed-state JSON, independent of installation exit code."""
import json
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from windows_client import installed_state as state


class WinGetStateTests(unittest.TestCase):
    def setUp(self):
        self.export = {"Sources": [{
            "SourceDetails": {"Name": "winget", "Type": "Microsoft.PreIndexed.Package"},
            "Packages": [{"PackageIdentifier": "Example.App", "Version": "1.2.3"},
                         {"PackageIdentifier": "Example.Other", "Version": "2.4.0"}]
        }]}

    def test_real_export_shape_exact_match(self):
        self.assertEqual(state.parse_export(self.export, "Example.App"), "1.2.3")
        self.assertIsNone(state.parse_export(self.export, "Example.Unknown"))
        self.assertEqual(state.numeric_version("1.2.3"), state.numeric_version("1.2.3.0"))

    def test_wrong_source_ignored(self):
        self.export["Sources"][0]["SourceDetails"]["Name"] = "msstore"
        self.assertIsNone(state.parse_export(self.export, "Example.App"))

    def test_missing_source_identity_fail_closed(self):
        del self.export["Sources"][0]["SourceDetails"]
        with self.assertRaises(state.StateError):
            state.parse_export(self.export, "Example.App")

    def test_ambiguous_and_unknown_versions_rejected(self):
        self.export["Sources"][0]["Packages"].append(
            {"PackageIdentifier": "Example.App", "Version": "1.2.3"})
        with self.assertRaises(state.StateError):
            state.parse_export(self.export, "Example.App")
        self.export["Sources"][0]["Packages"].pop()
        self.export["Sources"][0]["Packages"][0]["Version"] = "unknown"
        with self.assertRaises(state.StateError):
            state.parse_export(self.export, "Example.App")

    def test_no_prerelease_version_comparison_by_guess(self):
        for version in ("1.2", "latest", "1.2.3-alpha", "1.2.3;whoami"):
            with self.assertRaises(state.StateError):
                state.numeric_version(version)

    def test_real_json_file_readback_via_injected_official_runner(self):
        def fake_winget(command, **kwargs):
            self.assertEqual(command[:2], ["winget", "export"])
            self.assertIn("--include-versions", command)
            self.assertIn("--disable-interactivity", command)
            self.assertFalse(kwargs["shell"])
            self.assertFalse(kwargs["check"])
            output = Path(command[command.index("--output") + 1])
            output.write_text(json.dumps(self.export), encoding="utf-8")
            return SimpleNamespace(returncode=0)
        self.assertEqual(state.read_installed_version("Example.App", runner=fake_winget),
                         "1.2.3")

    def test_local_inventory_only_official_winget_without_install_approval(self):
        entries = state.parse_installed_inventory(self.export)
        self.assertEqual(entries, [
            {"id": "Example.App", "version": "1.2.3", "source": "winget"},
            {"id": "Example.Other", "version": "2.4.0", "source": "winget"},
        ])
        self.export["Sources"].append({
            "SourceDetails": {"Name": "msstore"},
            "Packages": [{"PackageIdentifier": "Microsoft.Store", "Version": "1.2.3"}]
        })
        self.assertEqual(state.parse_installed_inventory(self.export), entries)

    def test_ambiguous_and_poisoned_inventory_rejected(self):
        self.export["Sources"][0]["Packages"].append(
            {"PackageIdentifier": "Example.App", "Version": "1.2.3"})
        with self.assertRaises(state.StateError):
            state.parse_installed_inventory(self.export)
        self.export["Sources"][0]["Packages"].pop()
        self.export["Sources"][0]["Packages"][0]["PackageIdentifier"] = "Evil.App;cmd"
        with self.assertRaises(state.StateError):
            state.parse_installed_inventory(self.export)

    def test_local_inventory_export_is_temporary(self):
        temporary_file = []
        def fake(cmd, **kwargs):
            self.assertEqual(cmd[:2], ["winget", "export"])
            self.assertEqual(cmd[cmd.index("--source") + 1], "winget")
            self.assertFalse(kwargs["shell"])
            path = Path(cmd[cmd.index("--output") + 1])
            temporary_file.append(path)
            path.write_text(json.dumps(self.export), encoding="utf-8")
            return SimpleNamespace(returncode=0)
        result = state.read_installed_inventory(runner=fake)
        self.assertEqual(result[0]["id"], "Example.App")
        self.assertFalse(temporary_file[0].exists())

    def test_failed_export_rejected(self):
        with self.assertRaises(state.StateError):
            state.read_installed_version(
                "Example.App", runner=lambda *args, **kwargs: SimpleNamespace(returncode=1))


if __name__ == "__main__":
    unittest.main()
