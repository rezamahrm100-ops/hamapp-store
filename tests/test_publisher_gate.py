import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import publisher_gate as gate
import fdroid_bridge

APK_OUT = ('Verified using v2 scheme (APK Signature Scheme v2): true\n'
           'Number of signers: 1\n'
           'Signer #1 certificate SHA-256 digest: ' + 'a' * 64 + '\n')
BADGE = "package: name='ir.hamapp.example' versionCode='7' versionName='1.2.3'\n"


class MockRunner:
    def __init__(self, cert='a' * 64, package='ir.hamapp.example', versioncode=7, version='1.2.3', fail=False):
        self.cert, self.package, self.versioncode, self.version, self.fail = cert, package, versioncode, version, fail
        self.calls = []

    def __call__(self, command, **kwargs):
        self.calls.append(command)
        if self.fail:
            return subprocess.CompletedProcess(command, 1, '', 'invalid')
        if command[0] == 'apksigner':
            return subprocess.CompletedProcess(command, 0, 'Signer #1 certificate SHA-256 digest: ' + self.cert + '\n', '')
        if command[0] == 'aapt':
            out = f"package: name='{self.package}' versionCode='{self.versioncode}' versionName='{self.version}'\n"
            return subprocess.CompletedProcess(command, 0, out, '')
        return subprocess.CompletedProcess(command, 0, '', '')


class GateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = pathlib.Path(self.temp.name) / 'example.apk'
        self.path.write_bytes(b'not a real APK; tool mocked only')
        self.release = {'app_id': 'example', 'platform': 'android', 'version': '1.2.3',
                        'asset_url': 'https://github.com/rezamahrm100-ops/example-project/releases/download/v1.2.3/example.apk',
                        'sha256': hashlib.sha256(self.path.read_bytes()).hexdigest(), 'size_bytes': self.path.stat().st_size}
        self.candidate = {'release': self.release, 'source_repo': 'example-project', 'source_sha': 'a' * 40,
                          'package_id': 'ir.hamapp.example', 'version_code': 7}
        self.registry = {'schema_version': 1, 'publishers': [{'app_id': 'example', 'source_repo': 'example-project',
                          'platform': 'android', 'certificate_sha256': 'a' * 64, 'package_id': 'ir.hamapp.example'}]}

    def test_verified_but_not_publicly_approved(self):
        result = gate.verify(self.candidate, self.registry, self.path, runner=MockRunner())
        self.assertTrue(result['signature_verified'])
        self.assertFalse(result['public_release_authorized'])
        self.assertTrue(result['review_required'])

    def test_checked_in_registry_has_valid_schema(self):
        registry = json.loads((ROOT / 'catalog/trusted_signers.json').read_text(encoding='utf-8'))
        self.assertEqual(gate.validate_trust_registry(registry)['schema_version'], 1)

    def test_receipt_does_not_claim_source_sha_verified(self):
        receipt = gate.verify(self.candidate, self.registry, self.path, runner=MockRunner())
        self.assertFalse(receipt['source_commit_verified'])
        self.assertEqual(receipt['source_sha_claimed'], 'a' * 40)

    def test_reject_windows_missing_authenticode(self):
        if sys.platform != 'win32': self.skipTest('requires Windows')
        file = pathlib.Path(self.temp.name) / 'unsigned.exe'
        file.write_bytes(b'No valid Windows code signature')
        with self.assertRaises(gate.PublisherError):
            gate.verify_authenticode(file)

    def test_empty_production_registry_fail_closed(self):
        registry = json.loads((ROOT / 'catalog/trusted_signers.json').read_text(encoding='utf-8'))
        with self.assertRaises(gate.PublisherError):
            gate.verify(self.candidate, registry, self.path, runner=MockRunner())

    def test_mismatched_signer_rejected(self):
        with self.assertRaisesRegex(gate.PublisherError, 'signing certificate'):
            gate.verify(self.candidate, self.registry, self.path, runner=MockRunner(cert='b' * 64))

    def test_wrong_android_package_id(self):
        with self.assertRaisesRegex(gate.PublisherError, 'APK package'):
            gate.verify(self.candidate, self.registry, self.path, runner=MockRunner(package='evil.app'))

    def test_wrong_version_code(self):
        with self.assertRaises(gate.PublisherError):
            gate.verify(self.candidate, self.registry, self.path, runner=MockRunner(versioncode=8))

    def test_wrong_version_name(self):
        with self.assertRaises(gate.PublisherError):
            gate.verify(self.candidate, self.registry, self.path, runner=MockRunner(version='9.9.9'))

    def test_tool_exit_failure(self):
        with self.assertRaises(gate.PublisherError):
            gate.verify(self.candidate, self.registry, self.path, runner=MockRunner(fail=True))

    def test_hash_tamper_blocked_before_tools(self):
        self.path.write_bytes(self.path.read_bytes().replace(b'not', b'bad'))
        runner = MockRunner()
        with self.assertRaises(ValueError):
            gate.verify(self.candidate, self.registry, self.path, runner=runner)
        self.assertEqual(runner.calls, [])

    def test_source_repo_mismatch(self):
        self.candidate['source_repo'] = 'attacker'
        with self.assertRaises(gate.PublisherError):
            gate.validate_candidate(self.candidate, self.registry)

    def test_same_app_can_have_independent_android_and_windows_signers(self):
        windows = {"app_id": "example", "source_repo": "example-project",
                   "platform": "windows", "certificate_sha256": "b" * 64,
                   "package_id": None}
        self.registry["publishers"].append(windows)
        self.assertEqual(len(gate.validate_trust_registry(self.registry)["publishers"]), 2)
        self.assertEqual(gate.validate_candidate(self.candidate, self.registry)["platform"], "android")

    def test_duplicate_platform_publisher_still_rejected(self):
        self.registry["publishers"].append(dict(self.registry["publishers"][0]))
        with self.assertRaises(gate.PublisherError):
            gate.validate_trust_registry(self.registry)

    def test_duplicate_publisher_entries_fail_closed(self):
        self.registry['publishers'].append(dict(self.registry['publishers'][0]))
        with self.assertRaises(gate.PublisherError):
            gate.validate_candidate(self.candidate, self.registry)

    def test_unsigned_multi_signer_rejected(self):
        class Multi:
            def __call__(self, cmd, **kwargs):
                return subprocess.CompletedProcess(cmd, 0, APK_OUT + 'Signer #2 certificate SHA-256 digest: ' + 'b'*64, '')
        with self.assertRaises(gate.PublisherError):
            gate.verify_apk(self.path, 'ir.hamapp.example', 7, '1.2.3', runner=Multi())

    def test_source_commit_required(self):
        self.candidate['source_sha'] = 'main'
        with self.assertRaises(gate.PublisherError):
            gate.validate_candidate(self.candidate, self.registry)

    def test_invalid_versioncode_bool_rejected(self):
        self.candidate['version_code'] = True
        with self.assertRaises(gate.PublisherError):
            gate.validate_candidate(self.candidate, self.registry)

    def test_windows_fails_closed_on_nonwindows(self):
        if sys.platform == 'win32':
            self.skipTest('non-Windows only')
        with self.assertRaises(gate.PublisherError):
            gate.verify_authenticode(self.path)

    def _fdroid_policy(self):
        return {"schema_version": 1, "package_id": "ir.hamapp.example",
                "version_code": 7, "version_name": "1.2.3", "allowed_permissions": []}

    def _mock_verified_preflight(self):
        digest = self.candidate["release"]["sha256"]
        return {"developer_signature_and_github_provenance_checked": True,
                "verified_artifact_sha256": digest,
                "actual_archive": {"actual_archive_crc_and_paths_checked": True},
                "actual_android_permissions": {"requested_permissions_allowlist_checked": True},
                "actual_antivirus_signature_scan": {
                    "actual_signature_scan_completed_without_detection": True,
                    "artifact_sha256": digest},
                "public_distribution_authorized": False}

    def _private_workspace(self, name="private"):
        if sys.platform == "win32":
            self.skipTest("POSIX private key custody is required")
        workspace = pathlib.Path(self.temp.name) / name
        workspace.mkdir(mode=0o700)
        workspace.chmod(0o700)
        config = workspace / "config.yml"
        config.write_text("# dummy non-signing config\n", encoding="utf8")
        config.chmod(0o600)
        return workspace

    def _fake_verified_local_index(self, workspace, fingerprint, candidate):
        return {"local_index_signed_with_pinned_repository_key": True,
                "indexed_apk_sha256": candidate["release"]["sha256"],
                "repo_signer_fingerprint": fingerprint,
                "indexed_package_id": candidate["package_id"],
                "indexed_version_code": candidate["version_code"],
                "public_https_repository_verified": False}

    def _reviewed_stage(self, workspace, *, preflight=None, update_runner=None, index_verifier=None):
        if preflight is None:
            preflight = self._mock_verified_preflight()
        if update_runner is None:
            update_runner = lambda cmd, **opts: subprocess.CompletedProcess(cmd, 0, "", "")
        with patch.object(fdroid_bridge.owner_candidate_intake, "assess",
                          return_value=preflight) as assayed:
            result = fdroid_bridge.stage(
                self.candidate, self.registry, self.path, workspace,
                trusted_workflow="rezamahrm100-ops/example-project/.github/workflows/release.yml",
                trusted_source_ref="refs/tags/v1.2.3",
                permission_policy=self._fdroid_policy(),
                expected_repo_fingerprint="b"*64,
                index_verifier=(self._fake_verified_local_index if index_verifier is None else index_verifier),
                update_runner=update_runner)
        assayed.assert_called_once()
        self.assertEqual(assayed.call_args.kwargs["antivirus_scanner"], "clamscan")
        return result

    def test_fdroid_private_workspace_is_required(self):
        with self.assertRaises(gate.PublisherError):
            fdroid_bridge.stage(self.candidate, self.registry, self.path,
                                self.temp.name)
        if sys.platform == "win32":
            return
        workspace = self._private_workspace("private-symlink")
        link = workspace / "repo"
        try:
            link.symlink_to(self.path.parent, target_is_directory=True)
        except OSError:
            self.skipTest("symlink unavailable")
        with self.assertRaisesRegex(gate.PublisherError, "symlink"):
            self._reviewed_stage(workspace)

    def test_fdroid_requires_real_producer_and_manifest_policy(self):
        workspace = self._private_workspace("unverified")
        called = []
        def update(*args, **kwargs):
            called.append(args)
            return subprocess.CompletedProcess(args,0,"","")
        for kwargs in (
            {},
            {"trusted_workflow": "rezamahrm100-ops/example-project/.github/workflows/release.yml",
             "trusted_source_ref": "refs/tags/v1.2.3"},
            {"trusted_workflow": "attacker/repo/.github/workflows/release.yml",
             "trusted_source_ref": "refs/tags/v1.2.3",
             "permission_policy": self._fdroid_policy()},
            {"trusted_workflow": "rezamahrm100-ops/example-project/.github/workflows/release.yml",
             "trusted_source_ref": "refs/tags/v1.2.3",
             "permission_policy": self._fdroid_policy(),
             "antivirus_scanner": None}
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                fdroid_bridge.stage(self.candidate, self.registry, self.path, workspace,
                                    update_runner=update, **kwargs)
        self.assertEqual(called, [])
        self.assertFalse((workspace / "repo" / self.path.name).exists())

    def test_fdroid_real_preflight_failure_does_not_stage(self):
        workspace = self._private_workspace("failed-preflight")
        with patch.object(fdroid_bridge.owner_candidate_intake, "assess",
                          side_effect=ValueError("source attestation unavailable")):
            with self.assertRaisesRegex(ValueError, "source attestation"):
                fdroid_bridge.stage(
                    self.candidate, self.registry, self.path, workspace,
                    trusted_workflow="rezamahrm100-ops/example-project/.github/workflows/release.yml",
                    trusted_source_ref="refs/tags/v1.2.3",
                    permission_policy=self._fdroid_policy(),
                    expected_repo_fingerprint="b"*64)
        self.assertFalse((workspace / "repo" / self.path.name).exists())

    def test_fdroid_rejects_fake_antivirus_attestation_flags(self):
        workspace = self._private_workspace("fake-av")
        forged = self._mock_verified_preflight()
        forged["actual_antivirus_signature_scan"]["artifact_sha256"] = "d"*64
        with self.assertRaisesRegex(gate.PublisherError, "incomplete"):
            self._reviewed_stage(workspace, preflight=forged)
        self.assertFalse((workspace / "repo" / self.path.name).exists())

    def test_fdroid_staging_only_after_integrated_checks(self):
        workspace = self._private_workspace("success")
        def update(command, **kwargs):
            self.assertEqual(command, ["fdroid","update","--create-metadata"])
            self.assertEqual(pathlib.Path(kwargs["cwd"]).resolve(), workspace.resolve())
            return subprocess.CompletedProcess(command, 0, "", "")
        result = self._reviewed_stage(workspace, update_runner=update)
        self.assertFalse(result["deployed"])
        self.assertTrue(result["signed_source_and_signer_verified"])
        self.assertTrue(result["fresh_antivirus_signature_scan_verified"])
        self.assertTrue(result["private_index_v2_signature_and_exact_apk_verified"])
        self.assertFalse(result["public_https_repository_verified"])
        self.assertFalse(result["f_droid_signed_repository_independently_verified"])
        self.assertFalse(result["owner_approved_for_public_distribution"])
        self.assertTrue((workspace / "repo" / self.path.name).exists())

    def test_fdroid_rechecks_copied_file_after_preflight(self):
        workspace = self._private_workspace("tampered")
        def mutate_then_return(*args, **kwargs):
            self.path.write_bytes(b"changed after signed-source review")
            return self._mock_verified_preflight()
        with patch.object(fdroid_bridge.owner_candidate_intake, "assess",
                          side_effect=mutate_then_return):
            with self.assertRaises(gate.PublisherError):
                fdroid_bridge.stage(
                    self.candidate, self.registry, self.path, workspace,
                    trusted_workflow="rezamahrm100-ops/example-project/.github/workflows/release.yml",
                    trusted_source_ref="refs/tags/v1.2.3",
                    permission_policy=self._fdroid_policy(),
                    expected_repo_fingerprint="b"*64)
        self.assertFalse((workspace / "repo" / self.path.name).exists())

    def test_fdroid_upstream_update_failure_removes_new_file(self):
        workspace = self._private_workspace("update-failure")
        def failed(command, **kwargs):
            return subprocess.CompletedProcess(command, 1, "", "")
        with self.assertRaises(gate.PublisherError):
            self._reviewed_stage(workspace, update_runner=failed)
        self.assertFalse((workspace / "repo" / self.path.name).exists())
        self.assertTrue((workspace / "PUBLISHING_LOCKED_UNTIL_OWNER_REVIEW").exists())

    def test_fdroid_rejects_unverified_private_index_and_locks_workspace(self):
        workspace = self._private_workspace("missing-signed-index")
        def false_index(root, fingerprint, candidate):
            return {"local_index_signed_with_pinned_repository_key": False}
        with self.assertRaisesRegex(gate.PublisherError, "owner review required"):
            self._reviewed_stage(workspace, index_verifier=false_index)
        self.assertTrue((workspace / "PUBLISHING_LOCKED_UNTIL_OWNER_REVIEW").exists())
        self.assertFalse((workspace / "repo" / self.path.name).exists())
        with self.assertRaisesRegex(gate.PublisherError, "locked"):
            self._reviewed_stage(workspace)


if __name__ == "__main__":
    unittest.main()
