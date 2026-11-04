import sys
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from windows_client import winget_discovery as discovery


def result(text="", code=0):
    return SimpleNamespace(returncode=code, stdout=text, stderr="")


class ExternalWinGetTests(unittest.TestCase):
    def setUp(self):
        self.platform = patch.object(discovery, "_on_windows", return_value=True)
        self.platform.start()
        self.addCleanup(self.platform.stop)
        self.calls = []

    def runner(self, args, **kwargs):
        self.calls.append((args, kwargs))
        if args[1] == "search":
            return result(
                "Name                  Id                       Version   Source\n"
                "-----------------------------------------------------------------------\n"
                "Git                   Git.Git                  2.50.1    winget\n"
                "Visual Studio Code    Microsoft.VisualStudioCode  1.2.3   winget\n"
            )
        if args[1] == "show":
            return result("Found Git [Git.Git]\nVersion: 2.50.1\nPublisher: Git")
        return result()

    def test_search_source_pinned_and_ids_parsed_only_when_valid(self):
        found = discovery.search("Git", self.runner)
        self.assertEqual(found["source"], "winget")
        self.assertIn("Git.Git", [p["id"] for p in found["packages"]])
        self.assertFalse(found["results_are_owner_approved"])
        cmd, kw = self.calls[0]
        self.assertEqual(cmd[:4], ["winget", "search", "--query", "Git"])
        self.assertEqual(cmd[cmd.index("--source") + 1], "winget")
        self.assertFalse(kw["shell"])
        self.assertIn("--disable-interactivity", cmd)

    def test_unparseable_localized_header_cannot_create_actionable_id(self):
        discovered = discovery.search("foo", lambda *args, **kw:
                                      result("نام    شناسه    نسخه\nFake  E.Vil  9.0"))
        self.assertEqual(discovered["packages"], [])
        self.assertIn("E.Vil", discovered["output"])

    def test_input_rejections_prevent_command_dispatch(self):
        for invalid in ("-foo", "\n", "git\x00hack", "a" * 81, 123):
            with self.subTest(invalid=invalid), self.assertRaises(discovery.DiscoveryError):
                discovery.search(invalid, self.runner)
        for invalid in ("..evil", "Evil;whoami", "-id", "a..b", "a/b", "a", "a.b\n"):
            with self.subTest(id=invalid), self.assertRaises(discovery.DiscoveryError):
                discovery.show(invalid, self.runner)
        self.assertFalse(self.calls)

    def test_actual_package_show_is_source_exact(self):
        d = discovery.show("Git.Git", self.runner)
        self.assertFalse(d["hamapp_publisher_verified"])
        self.assertEqual(self.calls[0][0],
                         ["winget", "show", "--id", "Git.Git", "--exact",
                          "--source", "winget", "--disable-interactivity"])

    def test_non_windows_never_invokes_winget(self):
        with patch.object(discovery, "_on_windows", return_value=False):
            with self.assertRaises(discovery.DiscoveryError):
                discovery.search("Git", self.runner)
        self.assertFalse(self.calls)

    def test_install_requires_show_and_confirmed_absence_without_silent_flags(self):
        receipts = discovery.execute_external("Git.Git", "install",
                                               runner=self.runner,
                                               verifier=lambda _: None
                                               if sum(c[0][1] == "install" for c in self.calls) == 0
                                               else "2.50.1")
        self.assertEqual(receipts["installed_version_readback"], "2.50.1")
        self.assertFalse(receipts["hamapp_publisher_verified"])
        self.assertEqual([c[0][1] for c in self.calls], ["show", "install"])
        self.assertIn("--no-upgrade", self.calls[1][0])
        self.assertIn("--interactive", self.calls[1][0])
        for forbidden in ("--silent", "--ignore-security-hash", "--force",
                          "--accept-package-agreements", "--accept-source-agreements"):
            self.assertNotIn(forbidden, self.calls[1][0])
        self.assertFalse(self.calls[1][1]["shell"])

    def test_already_installed_rejects_reinstall(self):
        with self.assertRaises(discovery.DiscoveryError):
            discovery.execute_external("Git.Git", "install",
                                       runner=self.runner, verifier=lambda _: "2.50.1")
        self.assertEqual([c[0][1] for c in self.calls], ["show"])

    def test_upgrade_requires_existing_package(self):
        with self.assertRaises(discovery.DiscoveryError):
            discovery.execute_external("Git.Git", "upgrade",
                                       runner=self.runner, verifier=lambda _: None)
        self.assertEqual([c[0][1] for c in self.calls], ["show"])

    def test_runtime_failure_fails_closed(self):
        def failed(args, **kwargs):
            self.calls.append((args, kwargs))
            return result("not installed", code=1) if args[1] == "install" else result("Found Git")
        with self.assertRaises(discovery.DiscoveryError):
            discovery.execute_external("Git.Git", "install",
                                       runner=failed, verifier=lambda _: None)
        self.assertEqual(len(self.calls), 2)

    def test_no_post_install_readback_is_not_success(self):
        with self.assertRaises(discovery.DiscoveryError):
            discovery.execute_external("Git.Git", "install", runner=self.runner,
                                       verifier=lambda _: None)
        self.assertEqual([c[0][1] for c in self.calls], ["show", "install"])

    def test_show_error_does_not_enable_install(self):
        with self.assertRaises(discovery.DiscoveryError):
            discovery.execute_external("Git.Git", "install",
                runner=lambda args, **kw: result("no package", 1),
                verifier=lambda _: None)

    def test_source_unsupported_operations_rejected(self):
        with self.assertRaises(discovery.DiscoveryError):
            discovery.execute_external("Git.Git", "uninstall",
                                       runner=self.runner, verifier=lambda _: None)
        self.assertFalse(self.calls)


if __name__ == "__main__":
    unittest.main()
