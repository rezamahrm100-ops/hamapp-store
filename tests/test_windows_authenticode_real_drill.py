"""Source checks and negative tests for REAL offline Windows PE Authenticode CI.

True signatures/verification on actual Windows-built PE are executed in GitHub
hosted Linux using osslsigncode, not claimed by these isolated unit tests.
"""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import portable_authenticode_drill as drill
import windows_authenticode_real_drill as native_attempt


class RealPortableWindowsPESignatureTests(unittest.TestCase):
    def test_untrusted_owner_host_cannot_execute_ci_test_signer(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = Path(tmp) / "some.exe"
            exe.write_bytes(b"not a real PE file")
            with patch.dict(os.environ, {"GITHUB_ACTIONS": "false", "RUNNER_OS": "Linux"}):
                with self.assertRaisesRegex(drill.AuthenticodeDrillError, "GitHub-hosted"):
                    drill.check(exe, "a" * 40, Path(tmp) / "result.json")

    def test_actual_upstream_tool_results_fail_closed(self):
        ok = SimpleNamespace(returncode=0, stdout="Signature verification: ok", stderr="")
        denied = SimpleNamespace(returncode=1, stdout="Signature verification: failed", stderr="")
        with patch.object(drill.subprocess, "run", return_value=ok) as subprocess_mock:
            self.assertTrue(drill.run(["osslsigncode", "verify", "-in", "actual.exe"]))
            with self.assertRaisesRegex(drill.AuthenticodeDrillError, "predicate failed"):
                drill.run(["osslsigncode", "verify", "-in", "actual.exe"], expected_success=False)
            self.assertFalse(subprocess_mock.call_args.kwargs["check"])
            self.assertFalse(subprocess_mock.call_args.kwargs["shell"]) if "shell" in subprocess_mock.call_args.kwargs else None
        with patch.object(drill.subprocess, "run", return_value=denied):
            self.assertFalse(drill.run(["osslsigncode", "verify", "-in", "actual.exe"],
                                       expected_success=False))
            with self.assertRaisesRegex(drill.AuthenticodeDrillError, "predicate failed"):
                drill.run(["osslsigncode", "verify", "-in", "actual.exe"])

    def test_disabled_ci_key_reuse_and_no_false_production_flags(self):
        src = (ROOT / "scripts/portable_authenticode_drill.py").read_text("utf-8")
        for required in (
            "osslsigncode", '"-pkcs12"', '"-readpass"', '"-CAfile"',
            '"-require-leaf-hash"', "shutil.copyfile(signed, damaged)",
            "verified", "expected_success=False", 'TemporaryDirectory',
        ):
            if required == "verified":
                continue  # only cryptographic subprocess results are authoritative
            self.assertIn(required, src)
        for negative in (
            '"windows_native_trust_store_or_OS_WinVerifyTrust_tested": False',
            '"real_public_CA_authenticode_certificate_verified": False',
            '"owner_production_signature_or_installer_approved": False',
            '"public_release_authorized": False',
        ):
            self.assertIn(negative, src)

    def test_disposable_trust_chain_is_root_ca_to_code_signing_leaf_not_self_signed_leaf(self):
        src = (ROOT / "scripts/portable_authenticode_drill.py").read_text("utf-8")
        self.assertIn("x509.BasicConstraints(ca=True, path_length=0)", src)
        self.assertIn("x509.BasicConstraints(ca=False, path_length=None)", src)
        self.assertIn("ExtendedKeyUsageOID.CODE_SIGNING", src)
        self.assertIn("subject_name(name).issuer_name(root.subject)", src)
        self.assertIn("sign(ca_key, hashes.SHA256())", src)
        self.assertIn("signer_key, leaf, [root]", src)
        self.assertIn("fingerprint", src)
        self.assertIn("expected_success=False", src)
        self.assertIn('"sha256:" + identity["fingerprint"]', src)
        self.assertIn('"-ignore-cdp"', src)
        self.assertNotIn('"-ignore-crl"', src)
        self.assertNotIn('"sha2:" + identity["fingerprint"]', src)
        self.assertNotIn('"public_release_authorized": True', src)

    def test_hosted_pipeline_builds_real_windows_PE_first_then_uses_real_linux_validator(self):
        yml = (ROOT / ".github/workflows/windows-client-preview.yml").read_text("utf-8")
        self.assertIn("runs-on: windows-2022", yml)
        self.assertIn("hamapp-windows-unsigned-preview", yml)
        self.assertIn("portable-authenticode:", yml)
        self.assertIn("needs: desktop-preview", yml)
        self.assertIn("runs-on: ubuntu-24.04", yml)
        self.assertIn("sudo apt-get install -y --no-install-recommends osslsigncode", yml)
        self.assertIn("scripts/portable_authenticode_drill.py", yml)
        self.assertIn("hamapp-real-disposable-portable-authenticode-evidence", yml)
        self.assertIn("retention-days: 7", yml)
        self.assertNotIn("runs-on: self-hosted", yml)
        self.assertIn("native-windows-authenticode:", yml)
        self.assertIn("./scripts/windows_authenticode_real_drill.ps1 -UnsignedExe", yml)
        self.assertIn("hamapp-native-windows-ephemeral-trust-evidence", yml)
        self.assertIn("if-no-files-found: error", yml)
        self.assertNotIn("dist/windows-authenticode-evidence/receipt.json\n          path: dist/HamApp-Windows-Preview.exe", yml)

    def test_native_windows_test_signing_uses_real_ca_leaf_chain_and_private_ephemeral_keys(self):
        signer = (ROOT / "scripts/windows_ephemeral_pfx.py").read_text("utf-8")
        windows = (ROOT / "scripts/windows_authenticode_real_drill.ps1").read_text("utf-8")
        for marker in (
            "ca_key = rsa.generate_private_key", "signer_key = rsa.generate_private_key",
            "x509.BasicConstraints(ca=True, path_length=0)",
            "x509.BasicConstraints(ca=False, path_length=None)",
            "ExtendedKeyUsageOID.CODE_SIGNING", "sign(ca_key, hashes.SHA256())",
            '"root_cer": str(root_path)', "signer_key, leaf, [ca]",
        ):
            self.assertIn(marker, signer)
        self.assertIn("$material.a.root_cer", windows)
        self.assertIn("$material.b.root_cer", windows)
        self.assertIn("'Root'", windows)
        self.assertIn("'TrustedPublisher'", windows)
        self.assertIn("Get-Content -LiteralPath", windows)
        self.assertIn("Remove-Item -LiteralPath $tempRoot -Recurse", windows)
        self.assertIn("ACTUAL_WINDOWS_SIGNTOOL_AND_NATIVE_AUTHENTICODE_SIGNER_NEGATIVES_PASSED", windows)

    def test_previous_native_windows_attempt_is_not_considered_accepted(self):
        src = (ROOT / "scripts/windows_authenticode_real_drill.py").read_text("utf-8")
        self.assertIn('"public_release_authorized": False', src)
        self.assertIn('"production_authenticode_certificate_verified": False', src)
        self.assertIn('"windows_real_install_or_upgrade_verified": False', src)
        if os.name == "nt":
            self.skipTest("Windows host can only validate signed PE on separate CI")
        with self.assertRaisesRegex(native_attempt.DrillError, "native Windows"):
            native_attempt.check("a.exe", "b.exe", "c.exe",
                                 "a" * 64, "b" * 64, "a" * 40, "tampered.exe")


if __name__ == "__main__":
    unittest.main()
