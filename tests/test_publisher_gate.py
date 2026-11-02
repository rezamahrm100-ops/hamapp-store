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

    def test_fdroid_symlink_repo_rejected(self):
        workspace = pathlib.Path(self.temp.name) / 'private_link'
        workspace.mkdir()
        config = workspace / 'config.yml'
        config.write_text('# test only\n', encoding='utf8')
        if sys.platform != 'win32': config.chmod(0o600)
        link = workspace / 'repo'
        try: link.symlink_to(self.path.parent, target_is_directory=True)
        except OSError: self.skipTest('symlink unavailable')
        with self.assertRaisesRegex(gate.PublisherError, 'symlink'):
            fdroid_bridge.stage(self.candidate, self.registry, self.path, workspace, runner=MockRunner())

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

    def test_fdroid_rejects_missing_private_config(self):
        with self.assertRaisesRegex(gate.PublisherError, 'config.yml'):
            fdroid_bridge.stage(self.candidate, self.registry, self.path, self.temp.name, runner=MockRunner())

    def test_fdroid_staging_does_not_deploy(self):
        workspace = pathlib.Path(self.temp.name) / 'private'
        workspace.mkdir()
        config = workspace / 'config.yml'
        config.write_text('# test only\n', encoding='utf8')
        if sys.platform != 'win32': config.chmod(0o600)
        def fdroid(command, **kwargs):
            self.assertEqual(command, ['fdroid', 'update', '--create-metadata'])
            self.assertEqual(pathlib.Path(kwargs['cwd']).resolve(), workspace.resolve())
            return subprocess.CompletedProcess(command, 0, '', '')
        result = fdroid_bridge.stage(self.candidate, self.registry, self.path, workspace, runner=MockRunner(), update_runner=fdroid)
        self.assertFalse(result['deployed'])
        self.assertTrue((workspace / 'repo' / self.path.name).exists())

    def test_fdroid_rechecks_copied_file(self):
        workspace = pathlib.Path(self.temp.name) / 'private_toctou'
        workspace.mkdir()
        config = workspace / 'config.yml'
        config.write_text('# test only\n', encoding='utf8')
        if sys.platform != 'win32': config.chmod(0o600)
        source = self.path
        class MutatingRunner(MockRunner):
            def __call__(self, command, **kwargs):
                result = super().__call__(command, **kwargs)
                if command[0] == 'aapt': source.write_bytes(b'altered after initial hash')
                return result
        with self.assertRaisesRegex(gate.PublisherError, 'staging failed'):
            fdroid_bridge.stage(self.candidate, self.registry, self.path, workspace, runner=MutatingRunner())
        self.assertFalse((workspace / 'repo' / self.path.name).exists())

    def test_fdroid_failure_removes_new_file(self):
        workspace = pathlib.Path(self.temp.name) / 'private'
        workspace.mkdir()
        config = workspace / 'config.yml'
        config.write_text('# test only\n', encoding='utf8')
        if sys.platform != 'win32': config.chmod(0o600)
        def failed(command, **kwargs): return subprocess.CompletedProcess(command, 1, '', '')
        with self.assertRaises(gate.PublisherError):
            fdroid_bridge.stage(self.candidate, self.registry, self.path, workspace, runner=MockRunner(), update_runner=failed)
        self.assertFalse((workspace / 'repo' / self.path.name).exists())


if __name__ == '__main__': unittest.main()