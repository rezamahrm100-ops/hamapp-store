"""Fail-closed F-Droid Android handoff source and hosted toolchain policy tests."""
from pathlib import Path
import json
import subprocess
import shutil
import os
import unittest

ROOT=Path(__file__).resolve().parents[1]
ANDROID=ROOT/"android/app/src/main/java/ir/hamapp/store/InternalFdroidStore.java"
SCRIPT=ROOT/"scripts/fdroid_official_client_emulator.sh"

class OfficialFdroidHandoffTests(unittest.TestCase):
    def test_current_client_embeds_verified_index_not_external_launcher(self):
        src=ANDROID.read_text(encoding="utf-8")
        main=(ROOT/"android/app/src/main/java/ir/hamapp/store/MainActivity.java").read_text(encoding="utf-8")
        installer=(ROOT/"android/app/src/main/java/ir/hamapp/store/EmbeddedApkInstaller.java").read_text(encoding="utf-8")
        self.assertIn("InternalFdroidStore.openApproved(this, repo)", main)
        self.assertIn("EntryVerifier", src)
        self.assertIn("RepoPolicy.isAllowed(url, fingerprint)", src)
        self.assertIn("PackageInstaller.Session", installer)
        self.assertNotIn("FdroidEngine", main)
        self.assertNotIn("PublicFdroidSearch", main)

    def test_emulator_fixture_uses_real_canonical_fdroidrepos_host(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('dummy="fdroidrepos://example.invalid/', source)
        self.assertIn('example.invalid/fdroid/repo/?fingerprint=', source)
        self.assertNotIn('dummy="fdroidrepos://https://', source)

    def test_official_client_native_process_check_is_bounded_and_fail_closed(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("official_ready=false", source)
        self.assertIn("OFFICIAL_FDROID_INTENT_NATIVE_ACTIVITY_OR_PROCESS_NOT_READY", source)
        self.assertIn('if [[ "$official_ready" != true ]]; then', source)
        self.assertIn("adb shell pidof org.fdroid.fdroid", source)
        self.assertNotIn("adb shell pm grant", source)

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

    @unittest.skipUnless(os.name == "posix" and shutil.which("bash"), "POSIX bash parsing only")
    def test_bash_script_grammar(self):
        parsed=subprocess.run(["bash","-n",str(SCRIPT)],capture_output=True,text=True,timeout=10)
        self.assertEqual(parsed.returncode,0,parsed.stderr)

if __name__=="__main__":
    unittest.main()
