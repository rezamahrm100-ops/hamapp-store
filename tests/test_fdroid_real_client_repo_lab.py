"""Safe source guards and true XML-control choices for official F-Droid lab.

The actual signed repo + real upstream client network integration is a
separate hosted Android 33 workflow; these unit tests do not simulate success.
"""
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"scripts"))
import fdroid_client_accessible_ui as ui
import fdroid_client_private_repo_lab as lab
from fdroid_signed_repo_drill import DrillError


class RealFdroidClientLabTests(unittest.TestCase):
    def test_only_real_hosted_linux_and_immutable_two_version_contract(self):
        if os.name == "nt":
            with self.assertRaises(DrillError):
                lab.root()
        self.assertEqual(lab.PORT, 8975)
        self.assertEqual(lab.REPO_URL, "https://10.0.2.2:8975/fdroid/repo/")
        src=(ROOT/"scripts/fdroid_client_private_repo_lab.py").read_text("utf-8")
        self.assertIn('["fdroid", "init"]',src)
        self.assertIn('["fdroid", "update", "--create-metadata"]',src)
        self.assertIn("certified_fingerprint",src)
        self.assertIn("verify_signed_repo",src)
        self.assertIn("publish_files",src)
        self.assertIn('"source_sha"',src)
        self.assertNotIn("repo_private_key_uploaded",src)

    def test_private_signer_is_separate_from_public_repo_bytes(self):
        src=(ROOT/"scripts/fdroid_client_private_repo_lab.py").read_text("utf-8")
        self.assertIn('base / "signing" / "repo"',src)
        self.assertIn('base / "webroot" / "fdroid" / "repo"',src)
        self.assertIn('base / "signing" / "config.yml"',src)
        self.assertIn('path.suffix.lower() not in ALLOWED',src)
        self.assertNotIn('shutil.copytree(private',src)
        self.assertIn("info.st_nlink != 1",src)

    def test_real_temporary_https_signer_isolated_from_served_repository(self):
        source=(ROOT/"scripts/fdroid_client_private_repo_lab.py").read_text("utf-8")
        self.assertIn("make_ephemeral_https_identity(base)", source)
        self.assertIn("ExtendedKeyUsageOID.SERVER_AUTH", source)
        self.assertIn('x509.IPAddress(ipaddress.ip_address("10.0.2.2"))', source)
        self.assertIn('directory = base / "tls"', source)
        server=(ROOT/"scripts/fdroid_client_private_repo_server.py").read_text("utf-8")
        self.assertIn("ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)", server)
        self.assertIn("context.wrap_socket(server.socket", server)
        workflow=(ROOT/".github/workflows/fdroid-real-client-signed-repo.yml").read_text("utf-8")
        self.assertIn("-writable-system", workflow)
        self.assertIn('https://localhost:8975/', (ROOT/"scripts/fdroid_real_client_subscription_emulator.sh").read_text("utf-8"))

    def test_accessible_ui_only_taps_real_fdroid_package_visible_control(self):
        with tempfile.TemporaryDirectory() as t:
            f=Path(t)/"ui.xml"
            f.write_text('<hierarchy><node package="com.android.settings" clickable="true" '
                         'text="Allow" bounds="[10,20][90,80]"/>'
                         '<node package="org.fdroid.fdroid" clickable="true" '
                         'text="Enable" bounds="[100,200][300,260]"/></hierarchy>',encoding="utf-8")
            self.assertEqual(ui.select(f),(200,230))
            f.write_text('<hierarchy><node package="com.android.settings" clickable="true" '
                         'text="Enable" bounds="[0,0][100,100]"/></hierarchy>',encoding="utf-8")
            self.assertIsNone(ui.select(f))

    def test_real_client_network_reachability_is_distinct_from_install_claim(self):
        sh=(ROOT/"scripts/fdroid_real_client_subscription_emulator.sh").read_text("utf-8")
        self.assertIn('adb install -r "$RUNNER_TEMP/hamapp-official-fdroid/F-Droid.apk"',sh)
        self.assertIn('fdroidrepos://10.0.2.2:8975/fdroid/repo/',sh)
        self.assertIn('adb remount',sh)
        self.assertIn('adb disable-verity',sh)
        self.assertIn('adb reboot',sh)
        self.assertIn('sys.boot_completed',sh)
        self.assertIn('openssl x509 -subject_hash_old',sh)
        self.assertIn('DISPOSABLE_TEST_CA_INSTALLED_ON_ROOTED_EMULATOR_ONLY',sh)
        self.assertIn('scripts/fdroid_client_accessible_ui.py',sh)
        self.assertIn('request_count',sh)
        self.assertIn('"actual_fdroid_client_app_install_verified":False',sh)
        self.assertIn('"actual_fdroid_client_app_upgrade_verified":False',sh)
        self.assertIn('"official_client_repository_persisted_in_database_verified":False',sh)
        self.assertIn('"production_ready":False',sh)

    def test_signed_repo_v1_v2_job_never_runs_on_owner_or_uploads_keys(self):
        yaml=(ROOT/".github/workflows/fdroid-real-client-signed-repo.yml").read_text("utf-8")
        self.assertIn('runs-on: ubuntu-24.04',yaml)
        self.assertIn('api-level: 33',yaml)
        self.assertIn('fdroidserver==2.4.5',yaml)
        self.assertIn('scripts/fdroid_client_private_repo_lab.py',yaml)
        self.assertIn('scripts/fdroid_real_client_subscription_emulator.sh',yaml)
        self.assertIn('scripts/fdroid_official_client_emulator.sh prepare',yaml)
        self.assertNotIn('runs-on: self-hosted',yaml)
        self.assertNotIn('dist/android-two-version/v1.apk\n          if-no-files-found',yaml)


if __name__=="__main__":
    unittest.main()
