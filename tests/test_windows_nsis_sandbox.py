"""Strict reviewable source gates; actual NSIS install QA runs in hosted Windows job."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


class RealWindowsInstallerGateTests(unittest.TestCase):
    def test_unsigned_per_user_installer_cannot_request_elevation(self):
        src=(ROOT/"windows_installer/HamAppPreview.nsi").read_text("utf-8")
        self.assertIn("RequestExecutionLevel user",src)
        self.assertIn('InstallDir "$LOCALAPPDATA',src)
        self.assertIn('WriteRegDWORD HKCU',src)
        self.assertIn("IntCmp $0",src)
        self.assertIn("SetErrorLevel 14",src)
        self.assertIn('Abort "HamApp Preview downgrade was rejected"',src)
        self.assertIn('Section "Uninstall"',src)
        self.assertIn("DeleteRegKey HKCU",src)
        self.assertIn('File /oname=HamApp-Windows-Preview.exe',src)
        self.assertNotIn("HKLM",src)
        self.assertNotIn("RequestExecutionLevel admin",src)
        self.assertNotIn("ExecWait",src)
        self.assertNotIn("http://",src)
        self.assertNotIn("https://",src)

    def test_only_ephemeral_hosted_windows_can_run_install_verification(self):
        src=(ROOT/"scripts/windows_nsis_sandbox_acceptance.ps1").read_text("utf-8")
        for expected in (
            "$env:GITHUB_ACTIONS -ne 'true'", "$env:RUNNER_OS -ne 'Windows'",
            "$env:RUNNER_TEMP", "Start-Process", "Get-FileHash",
            "VersionCode", "actual_hosted_windows_v2_installer_upgrade_passed",
            "actual_older_installer_downgrade_refused", "uninstall",
            "product_binary_v2_content_change_verified = $false",
            "native_installer_authenticode_production_verified = $false",
            "public_release_approved = $false",
        ):
            self.assertIn(expected,src)
        self.assertNotIn("HKLM",src)
        self.assertNotIn("Remove-Item -Path C:",src)

    def test_actual_hosted_pipeline_reuses_exact_previous_native_exe(self):
        src=(ROOT/".github/workflows/windows-client-preview.yml").read_text("utf-8")
        self.assertIn("nsis-installer-sandbox:",src)
        self.assertIn("needs: desktop-preview",src)
        self.assertIn("runs-on: windows-2022",src)
        self.assertIn("choco install nsis --version=3.11.0",src)
        self.assertIn("actions/download-artifact@v4",src)
        self.assertIn("hamapp-windows-unsigned-preview",src)
        self.assertIn("scripts/windows_nsis_sandbox_acceptance.ps1",src)
        self.assertIn("hamapp-real-hosted-nsis-install-qa",src)
        self.assertNotIn("runs-on: self-hosted",src)


if __name__=="__main__":
    unittest.main()
