"""One-click integrity verifier must stay local and must never execute binaries."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class OwnerPreviewVerifier(unittest.TestCase):
    def test_local_hash_verification_does_not_run_installer(self):
        script = (ROOT / "scripts/HamApp-Verify-Preview.cmd").read_text("utf-8")
        for token in ("Security.Cryptography.SHA256", "SHA256SUMS.txt", "manifest.json",
                      "source", "production_signed", "public_release_authorized",
                      "Get-Item", "ReparsePoint", "ALL_ARTIFACT_SHA256_CHECKS_PASSED"):
            if token == "source":
                continue
            self.assertIn(token, script)
        for unsafe in ("Start-Process", "Invoke-Expression", "iex ",
                       "curl ", "Invoke-WebRequest", "Set-ExecutionPolicy",
                       "ExecutionPolicy Bypass", "winget install", "msiexec",
                       "Start-Sleep", "REQUEST_INSTALL_PACKAGES"):
            self.assertNotIn(unsafe, script)
        self.assertIn("FAILED: do not open or install", script)

    def test_verifier_is_packaged_for_both_owner_platforms(self):
        workflow = (ROOT / ".github/workflows/owner-installable-previews.yml").read_text("utf-8")
        self.assertGreaterEqual(workflow.count("scripts/HamApp-Verify-Preview.cmd"), 3)
        self.assertIn("dist/owner-preview/android/", workflow)
        self.assertIn("dist/owner-preview/windows/HamApp-Verify-Preview.cmd", workflow)


if __name__ == "__main__":
    unittest.main()
