"""Owner runner remains on trusted main and only performs read-only checks."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class OwnerRunnerIsolation(unittest.TestCase):
    def test_self_host_is_only_trusted_main(self):
        src = (ROOT / ".github/workflows/windows-qa.yml").read_text("utf-8")
        self.assertIn("branches: [main]", src)
        self.assertNotIn("pull_request:", src)
        self.assertNotIn("pull_request_target:", src)
        self.assertNotIn("workflow_run:", src)
        self.assertIn("github.ref == 'refs/heads/main'", src)
        self.assertIn("runs-on: [self-hosted, Windows, X64, hamapp-windows]", src)
        self.assertIn("contents: read", src)
        self.assertIn("persist-credentials: false", src)
        self.assertIn("cancel-in-progress: false", src)
        self.assertIn("windows_client/**", src)
        self.assertIn("winget.exe --version", src)
        self.assertNotIn("winget.exe install", src)
        self.assertNotIn("winget.exe uninstall", src)
        self.assertNotIn("--accept-package-agreements", src)


if __name__ == "__main__":
    unittest.main()
