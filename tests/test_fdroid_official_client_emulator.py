"""Fail-closed F-Droid Android handoff source and hosted toolchain policy tests."""
from pathlib import Path
import json
import subprocess
import shutil
import unittest

ROOT=Path(__file__).resolve().parents[1]
ANDROID=ROOT/"android/app/src/main/java/ir/hamapp/store/MainActivity.java"
SCRIPT=ROOT/"scripts/fdroid_official_client_emulator.sh"

class OfficialFdroidHandoffTests(unittest.TestCase):
    def test_source_invokes_official_client_not_arbitrary_browser(self):
        src=ANDROID.read_text(encoding="utf-8")
        self.assertIn('Uri.parse("fdroidrepos://" + pinnedRepoUrl)',src)
        self.assertIn('intent.setPackage("org.fdroid.fdroid")',src)
        self.assertIn('if (!RepoPolicy.isAllowed(url, fingerprint))',src)
        self.assertIn('appendQueryParameter("fingerprint"',src)
        self.assertIn("new AlertDialog.Builder(this)",src)
        self.assertNotIn('new Intent(Intent.ACTION_VIEW, uri)',src)
        self.assertNotIn("ACTION_INSTALL_PACKAGE",src)

    def test_unapproved_storefront_has_no_downloads(self):
        repo=json.loads((ROOT/"catalog/android_repository.json").read_text(encoding="utf-8"))
        self.assertIsNone(repo["repository"])
        apps=json.loads((ROOT/"catalog/apps.json").read_text(encoding="utf-8"))["apps"]
        self.assertTrue(all(a["status"]=="planned" for a in apps))

    def test_hosted_only_real_client_crypto_pins_and_negative_release_claims(self):
        src=SCRIPT.read_text(encoding="utf-8")
        self.assertIn('GITHUB_ACTIONS',src)
        self.assertIn('37D2C98789D8311948394E3E41E7044E1DBA2E89',src)
        self.assertIn('43238d512c1e5eb2d6569f4a3afbf5523418b82e0a3ed1552770abb9a9c9ccab',src)
        self.assertIn('gpg --batch --homedir "$base/gnupg" --verify',src)
        self.assertIn('"$apksigner" verify',src)
        self.assertIn('example.invalid',src)
        self.assertIn('"official_client_app_install_or_update_verified":False',src)
        self.assertIn('"production_ready":False',src)
        self.assertNotIn('adb shell pm grant',src)

    @unittest.skipUnless(shutil.which("bash"), "bash not on this hosted operating system")
    def test_bash_script_grammar(self):
        parsed=subprocess.run(["bash","-n",str(SCRIPT)],capture_output=True,text=True,timeout=10)
        self.assertEqual(parsed.returncode,0,parsed.stderr)

if __name__=="__main__":
    unittest.main()
