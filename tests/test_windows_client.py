"""Tests for fail-closed desktop catalogue and interactive winget contract."""
import copy
import json
import pathlib
import sys
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from windows_client import core
import build_windows_client_catalog as builder


class WindowsClientTests(unittest.TestCase):
    def setUp(self):
        self.sample = {"schema_version": 1, "apps": [
            {"id": "demo-app", "name_fa": "برنامهٔ نمونه", "description": "فقط آزمون",
             "status": "planned", "version": None, "winget_id": None}]}

    def test_client_catalogue_accepts_planned(self):
        self.assertIs(core.validate_manifest(self.sample), self.sample)

    def test_client_rejects_planned_with_installer(self):
        self.sample["apps"][0]["winget_id"] = "Example.Publisher"
        with self.assertRaises(core.ClientError):
            core.validate_manifest(self.sample)

    def test_client_rejects_duplicate_ids(self):
        self.sample["apps"].append(dict(self.sample["apps"][0]))
        with self.assertRaises(core.ClientError):
            core.validate_manifest(self.sample)

    def test_client_rejects_arbitrary_command_fields(self):
        self.sample["apps"][0]["command"] = "powershell -enc XYZ"
        with self.assertRaises(core.ClientError):
            core.validate_manifest(self.sample)

    def test_client_disallows_installing_planned(self):
        with patch.object(core.sys, "platform", "win32"):
            with self.assertRaises(core.ClientError):
                core.command_for(self.sample["apps"][0], "install")

    def test_client_disallows_non_windows(self):
        with patch.object(core.sys, "platform", "linux"):
            with self.assertRaises(core.ClientError):
                core.command_for(self.sample["apps"][0], "install")

    def test_client_rejects_shell_injection(self):
        sample = dict(self.sample["apps"][0], status="available", version="1.2.3",
                      winget_id="Example.App;Start-Process")
        with patch.object(core.sys, "platform", "win32"):
            with self.assertRaises(core.ClientError):
                core.command_for(sample, "install")

    def test_client_rejects_version_shell_injection(self):
        sample = dict(self.sample["apps"][0], status="available", version="1.2.3;whoami",
                      winget_id="Example.App")
        with patch.object(core.sys, "platform", "win32"):
            with self.assertRaises(core.ClientError):
                core.command_for(sample, "install")

    def test_client_only_expected_winget_args(self):
        sample = dict(self.sample["apps"][0], status="available", version="1.2.3",
                      winget_id="Example.App")
        with patch.object(core.sys, "platform", "win32"):
            self.assertEqual(core.command_for(sample, "install"),
                ["winget", "install", "--id", "Example.App", "--exact", "--source", "winget",
                 "--version", "1.2.3", "--interactive"])
            self.assertEqual(core.command_for(sample, "upgrade"),
                ["winget", "upgrade", "--id", "Example.App", "--exact", "--source", "winget",
                 "--version", "1.2.3", "--interactive"])
            self.assertEqual(core.command_for(sample, "show"),
                ["winget", "show", "--id", "Example.App", "--exact", "--source", "winget"])

    def test_production_map_is_empty_and_store_safe(self):
        with (ROOT / "catalog/winget_packages.json").open(encoding="utf-8") as f:
            self.assertEqual(json.load(f)["packages"], [])
        from subprocess import run
        proc = run([sys.executable, str(ROOT / "scripts/build_windows_client_catalog.py")],
                   cwd=ROOT, capture_output=True, text=True, timeout=45)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        generated = json.loads((ROOT / "dist/windows-client/windows-client-catalog.json").read_text(encoding="utf-8"))
        self.assertTrue(all(a["status"] == "planned" for a in generated["apps"]))
        core.validate_manifest(generated)


class SourceMapTests(unittest.TestCase):
    def setUp(self):
        self.catalog = {"schema_version": 1, "apps": [{
            "id": "demo", "name_fa": "نمونه", "name_en": "Demo", "description": "Test",
            "platforms": ["windows"], "status": "released", "version": "1.2.3",
            "download_url": "https://github.com/rezamahrm100-ops/demo-project/releases/download/v1.2.3/demo.exe",
            "release_proof": {"sha256": "a" * 64, "size_bytes": 100, "certificate_sha256": "b" * 64,
                              "source_repo": "demo-project", "package_id": None, "version_code": None}}]}
        self.registry = {"schema_version": 1, "publishers": [{
            "app_id": "demo", "source_repo": "demo-project", "platform": "windows",
            "certificate_sha256": "b" * 64, "package_id": None}]}
        self.history = {"schema_version": 1, "releases": [{
            "app_id": "demo", "platform": "windows", "version": "1.2.3",
            "version_code": None, "source_repo": "demo-project", "package_id": None,
            "certificate_sha256": "b" * 64, "artifact_sha256": "a" * 64,
            "status": "approved"}], "revoked_signers": []}
        self.mapping = {"schema_version": 1, "packages": [{
            "app_id": "demo", "winget_id": "Example.App", "version": "1.2.3",
            "artifact_sha256": "a" * 64}]}

    def test_approved_fixture_builds(self):
        result = builder.build(self.catalog, self.registry, self.history, self.mapping)
        self.assertEqual(result["apps"][0]["status"], "available")
        self.assertEqual(result["apps"][0]["winget_id"], "Example.App")

    def test_no_mapping_cannot_install(self):
        self.mapping["packages"] = []
        self.assertEqual(builder.build(self.catalog, self.registry, self.history, self.mapping)["apps"][0]["status"], "planned")

    def test_source_hash_mismatch_fails(self):
        self.mapping["packages"][0]["artifact_sha256"] = "d" * 64
        with self.assertRaises(ValueError):
            builder.build(self.catalog, self.registry, self.history, self.mapping)

    def test_mapping_in_wrong_version_fails(self):
        self.mapping["packages"][0]["version"] = "0.9.0"
        with self.assertRaises(ValueError):
            builder.build(self.catalog, self.registry, self.history, self.mapping)

    def test_bad_id_rejected(self):
        self.mapping["packages"][0]["winget_id"] = "Example.App && whoami"
        with self.assertRaises(ValueError):
            builder.build(self.catalog, self.registry, self.history, self.mapping)

    def test_revoked_identity_rejected(self):
        self.history["revoked_signers"] = ["b" * 64]
        with self.assertRaises(ValueError):
            builder.build(self.catalog, self.registry, self.history, self.mapping)

    def test_nonapproved_release_rejected(self):
        self.history["releases"][0]["status"] = "revoked"
        with self.assertRaises(ValueError):
            builder.build(self.catalog, self.registry, self.history, self.mapping)

    def test_map_nonexistent_release_rejected(self):
        self.catalog["apps"] = []
        with self.assertRaises(ValueError):
            builder.build(self.catalog, self.registry, self.history, self.mapping)

    def test_map_duplicate_rejected(self):
        self.mapping["packages"].append(copy.deepcopy(self.mapping["packages"][0]))
        with self.assertRaises(ValueError):
            builder.build(self.catalog, self.registry, self.history, self.mapping)

    def test_no_mapping_never_triggers_real_install(self):
        self.mapping["packages"] = []
        output = builder.build(self.catalog, self.registry, self.history, self.mapping)
        with patch.object(core.sys, "platform", "win32"):
            with self.assertRaises(core.ClientError):
                core.command_for(output["apps"][0], "install")


if __name__ == "__main__":
    unittest.main()
