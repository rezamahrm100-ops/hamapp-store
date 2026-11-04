import pathlib
import sys
import tempfile
import unittest
from subprocess import CompletedProcess
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import android_permission_review as p


class PermissionReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.apk=pathlib.Path(self.tmp.name)/"test.apk"
        self.apk.write_bytes(b"synthetic-only-APK-bytes")
        self.policy={"schema_version":1,"package_id":"ir.hamapp.store","version_code":1,
                     "version_name":"0.1.0-preview","allowed_permissions":[]}
        self.badging="package: name='ir.hamapp.store' versionCode='1' versionName='0.1.0-preview'\n"
        self.permissions="package: ir.hamapp.store\n"

    def runner(self,cmd,**kwargs):
        self.assertFalse(kwargs["shell"])
        self.assertFalse(kwargs["check"])
        self.assertEqual(cmd[:2],["aapt","dump"])
        return CompletedProcess(cmd,0,self.badging if cmd[2]=="badging" else self.permissions,"")

    def test_no_permissions_accepted_but_no_malware_or_signer_claims(self):
        result=p.review(self.apk,self.policy,runner=self.runner)
        self.assertTrue(result["requested_permissions_allowlist_checked"])
        self.assertFalse(result["malware_free_verified"])
        self.assertFalse(result["code_signature_verified"])
        self.assertFalse(result["production_release_authorized"])
        self.assertEqual(result["requested_permissions"],[])

    def test_unexpected_privileged_permission_rejected(self):
        self.permissions="package: ir.hamapp.store\nuses-permission: name='android.permission.REQUEST_INSTALL_PACKAGES'\n"
        with self.assertRaises(p.AndroidPermissionError):
            p.review(self.apk,self.policy,runner=self.runner)

    def test_exact_androidx_app_signature_receiver_guard_only(self):
        allowed = "ir.hamapp.store.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"
        self.policy["allowed_permissions"] = [allowed]
        self.permissions = ("package: ir.hamapp.store\n"
                            "uses-permission: name='" + allowed + "'\n")
        receipt = p.review(self.apk, self.policy, runner=self.runner)
        self.assertEqual(receipt["requested_permissions"], [allowed])
        for wrong in (
                "ir.other.store.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION",
                "ir.hamapp.store.ANY_PERMISSION",
                "android.permission.REQUEST_INSTALL_PACKAGES"):
            with self.subTest(wrong=wrong):
                self.permissions = "uses-permission: name='" + wrong + "'\n"
                with self.assertRaises(p.AndroidPermissionError):
                    p.review(self.apk, self.policy, runner=self.runner)

    def test_permission_allowlist_must_be_explicit(self):
        self.policy["allowed_permissions"]=["android.permission.INTERNET"]
        self.permissions="package: ir.hamapp.store\nuses-permission: name='android.permission.INTERNET'\n"
        self.assertEqual(p.review(self.apk,self.policy,runner=self.runner)["requested_permissions"],
                         ["android.permission.INTERNET"])

    def test_duplicate_or_unknown_permission_output_fails_closed(self):
        self.permissions="uses-permission: name='android.permission.INTERNET'\n"*2
        with self.assertRaises(p.AndroidPermissionError):
            p.parse_requested_permissions(self.permissions)
        self.permissions="uses-permission: name='evil.permission.TRACK'\n"
        with self.assertRaises(p.AndroidPermissionError):
            p.parse_requested_permissions(self.permissions)

    def test_app_identity_and_version_must_match(self):
        self.policy["version_code"]=2
        with self.assertRaises(p.AndroidPermissionError):
            p.review(self.apk,self.policy,runner=self.runner)

    def test_invalid_policy_rejected(self):
        self.policy["allowed_permissions"]=["android.permission.INTERNET"]*2
        with self.assertRaises(p.AndroidPermissionError):
            p.validate_policy(self.policy)

    def test_symlink_apk_rejected(self):
        link=self.apk.parent/"link.apk"
        try:
            link.symlink_to(self.apk)
        except OSError:
            self.skipTest("no symlink")
        with self.assertRaises(p.AndroidPermissionError):
            p.review(link,self.policy,runner=self.runner)


if __name__=="__main__":
    unittest.main()
