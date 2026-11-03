"""Explicit Windows Authenticode integration policy and no-production tests.

The genuine signing + OS cryptographic validation happens in hosted Windows
workflows. These source tests protect refusal boundaries on other hosts.
"""
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import windows_authenticode_real_drill as drill

class RealNativeSignaturePolicyTests(unittest.TestCase):
    def test_native_windows_os_is_required(self):
        if os.name == "nt":
            self.skipTest("native Windows actually exercised in hosted workflow")
        with self.assertRaisesRegex(drill.DrillError,"native Windows"):
            drill.check("a.exe","b.exe","c.exe","a"*64,"b"*64,"a"*40,"tampered.exe")

    def test_invalid_signing_identity_rejected_even_on_windows(self):
        if os.name!="nt":
            self.skipTest("Windows-only target validation")
        with self.assertRaises(ValueError):
            drill.check("a","b","c","bad fingerprint","b"*64,"a"*40,"z")

    def test_real_script_uses_os_signature_and_exact_artifact_review(self):
        src=(ROOT/"scripts/windows_authenticode_real_drill.py").read_text("utf-8")
        self.assertIn("publisher_gate.verify_authenticode(signed)",src)
        self.assertIn("publisher_gate.verify_authenticode(foreign)",src)
        self.assertIn("publisher_gate.verify(candidate, registry, signed)",src)
        self.assertIn("publisher_gate.verify(foreign_candidate, registry, foreign)",src)
        self.assertIn("publisher_gate.verify(candidate, registry, target)",src)
        self.assertIn('"public_release_authorized": False',src)
        self.assertIn('"production_authenticode_certificate_verified": False',src)
        self.assertIn('"windows_real_install_or_upgrade_verified": False',src)

    def test_temp_signer_cannot_run_on_owner_device_and_does_not_upload_secrets(self):
        ps=(ROOT/"scripts/windows_authenticode_real_drill.ps1").read_text("utf-8")
        self.assertIn("$env:GITHUB_ACTIONS -ne 'true'",ps)
        self.assertIn("CertificateRequest",ps)
        self.assertIn("CreateSelfSigned",ps)
        self.assertIn("X509EnhancedKeyUsageExtension",ps)
        self.assertNotIn("New-SelfSignedCertificate @opts",ps)
        self.assertIn("Set-AuthenticodeSignature",ps)
        self.assertIn("CurrentUser",ps)
        self.assertNotIn("LocalMachine",ps)
        self.assertIn("Remove-Item",ps)
        yml=(ROOT/".github/workflows/windows-client-preview.yml").read_text("utf-8")
        self.assertIn("runs-on: windows-latest",yml)
        self.assertIn("hamapp-windows-unsigned-preview",yml)
        self.assertIn("hamapp-real-ephemeral-windows-authenticode-evidence",yml)
        self.assertNotIn("runs-on: self-hosted",yml)

if __name__=="__main__":
    unittest.main()
