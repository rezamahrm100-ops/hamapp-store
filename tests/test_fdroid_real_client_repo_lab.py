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
                         'text="Refresh" bounds="[100,200][300,260]"/></hierarchy>',encoding="utf-8")
            self.assertEqual(ui.select(f),(200,230))
            # Real failed emulator #41653381148 showed "Adding repository"
            # because generic select had already clicked the Add button.
            # Only the dedicated selector may make that authorization tap.
            f.write_text('<hierarchy><node package="org.fdroid.fdroid" clickable="true" '
                         'text="Add repository" bounds="[100,200][300,260]"/></hierarchy>',
                         encoding="utf-8")
            self.assertIsNone(ui.select(f))
            self.assertEqual(ui.select_actual_repository_add(f),(200,230))
            f.write_text('<hierarchy><node package="org.fdroid.fdroid" clickable="true" '
                         'text="Allow" bounds="[100,200][300,260]"/></hierarchy>',
                         encoding="utf-8")
            self.assertIsNone(ui.select(f))
            f.write_text('<hierarchy><node package="com.android.settings" clickable="true" '
                         'text="Enable" bounds="[0,0][100,100]"/></hierarchy>',encoding="utf-8")
            self.assertIsNone(ui.select(f))

    def test_real_fdroid_add_repository_button_requires_actual_clickable_app_node(self):
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/"official-add-repo.xml"
            path.write_text(
                '<hierarchy>'
                '<node package="org.fdroid.fdroid" text="Add repository" clickable="false" '
                'bounds="[16,30][210,85]"/>'
                '<node package="org.fdroid.fdroid" text="Add repository" clickable="true" '
                'bounds="[160,188][304,230]"/>'
                '</hierarchy>',encoding="utf-8")
            self.assertEqual(ui.select_actual_repository_add(path),(232,209))
            path.write_text(
                '<hierarchy><node package="com.google.android.permissioncontroller" '
                'text="Add repository" clickable="true" bounds="[160,188][304,230]"/>'
                '</hierarchy>',encoding="utf-8")
            self.assertIsNone(ui.select_actual_repository_add(path))
            path.write_text(
                '<hierarchy><node package="org.fdroid.fdroid" '
                'text="Add repository" clickable="false" bounds="[160,188][304,230]"/>'
                '</hierarchy>',encoding="utf-8")
            self.assertIsNone(ui.select_actual_repository_add(path))

    def test_real_fdroid_nested_button_label_taps_clickable_parent_only(self):
        # Actual official F-Droid screenshot confirms a blue Add repository
        # button, but UIAutomator may expose its label as a child TextView.
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/"nested-add-repository.xml"
            path.write_text(
                '<hierarchy>'
                '<node package="org.fdroid.fdroid" text="" clickable="false" '
                'bounds="[0,0][320,600]">'
                '<node package="org.fdroid.fdroid" text="Add repository" '
                'clickable="false" bounds="[30,42][220,78]"/>'
                '<node package="org.fdroid.fdroid" text="" clickable="true" '
                'bounds="[160,188][304,228]">'
                '<node package="org.fdroid.fdroid" text="Add repository" '
                'clickable="false" bounds="[178,195][287,221]"/>'
                '</node></node></hierarchy>', encoding="utf-8")
            self.assertEqual(ui.select_actual_repository_add(path), (232,208))
            path.write_text(
                '<hierarchy><node package="org.fdroid.fdroid" clickable="true" '
                'bounds="[0,0][320,600]">'
                '<node package="org.fdroid.fdroid" text="Add repository" '
                'clickable="false" bounds="[12,20][210,72]"/>'
                '</node></hierarchy>', encoding="utf-8")
            self.assertIsNone(ui.select_actual_repository_add(path))
            path.write_text(
                '<hierarchy><node package="com.android.settings" clickable="true" '
                'bounds="[160,188][304,228]">'
                '<node package="org.fdroid.fdroid" text="Add repository" '
                'clickable="false" bounds="[180,195][290,220]"/>'
                '</node></hierarchy>', encoding="utf-8")
            self.assertIsNone(ui.select_actual_repository_add(path))

    def test_actual_fdroid_filter_tooltip_dismissal_is_bounded_and_owned(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"live-ui.xml"
            path.write_text(
                '<hierarchy><node package="org.fdroid.fdroid" clickable="true" '
                'bounds="[160,220][300,264]">'
                '<node package="org.fdroid.fdroid" text="Got it" clickable="false" '
                'bounds="[195,228][270,256]"/></node></hierarchy>',encoding="utf-8")
            self.assertEqual(ui.select_onboarding_hint_dismissal(path),(230,242))
            path.write_text(
                '<hierarchy><node package="org.fdroid.fdroid" text="Got it" '
                'clickable="false" bounds="[160,220][300,264]"/></hierarchy>',encoding="utf-8")
            self.assertIsNone(ui.select_onboarding_hint_dismissal(path))
            path.write_text(
                '<hierarchy><node package="com.android.permissioncontroller" '
                'text="Got it" clickable="true" bounds="[160,220][300,264]"/>'
                '</hierarchy>',encoding="utf-8")
            self.assertIsNone(ui.select_onboarding_hint_dismissal(path))
            path.write_text(
                '<hierarchy><node package="org.fdroid.fdroid" text="Got it" '
                'clickable="true" bounds="[0,0][320,800]"/></hierarchy>',encoding="utf-8")
            self.assertIsNone(ui.select_onboarding_hint_dismissal(path))

    def test_android_system_notification_overlay_is_denied_only_when_actual_ui_matches(self):
        with tempfile.TemporaryDirectory() as temporary:
            xml=Path(temporary)/"system-notification.xml"
            xml.write_text(
                '<hierarchy>'
                '<node package="com.google.android.permissioncontroller" '
                'text="Allow F-Droid to send you notifications?" clickable="false" '
                'bounds="[30,100][320,200]"/>'
                '<node package="com.google.android.permissioncontroller" '
                'text="Don\'t allow" clickable="true" bounds="[48,392][272,454]"/>'
                '</hierarchy>', encoding="utf-8")
            self.assertEqual(ui.select_unneeded_notification_denial(xml),(160,423))
            self.assertIsNone(ui.select(xml))
            xml.write_text(
                '<hierarchy><node package="com.google.android.permissioncontroller" '
                'text="Allow a different app to send you notifications?" clickable="false"/>'
                '<node package="com.google.android.permissioncontroller" '
                'text="Don\'t allow" clickable="true" bounds="[48,392][272,454]"/>'
                '</hierarchy>', encoding="utf-8")
            self.assertIsNone(ui.select_unneeded_notification_denial(xml))
            xml.write_text(
                '<hierarchy><node package="org.fdroid.fdroid" '
                'text="Allow F-Droid to send you notifications?" clickable="false"/>'
                '<node package="org.fdroid.fdroid" '
                'text="Don\'t allow" clickable="true" bounds="[48,392][272,454]"/>'
                '</hierarchy>', encoding="utf-8")
            self.assertIsNone(ui.select_unneeded_notification_denial(xml))

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
        self.assertIn('scripts/fdroid_official_inclient_install_emulator.py --stage 1',sh)
        self.assertIn('scripts/fdroid_official_inclient_install_emulator.py --stage 2',sh)
        self.assertIn('--deny-notification-prompt',sh)
        self.assertIn('--dismiss-onboarding',sh)
        self.assertIn('OFFICIAL_FDROID_REAL_ONBOARDING_TIP_DISMISSED',sh)
        self.assertIn('--confirm-repository-add',sh)
        self.assertIn('OFFICIAL_FDROID_NATIVE_ADD_REPOSITORY_BUTTON_ACTUALLY_TAPPED',sh)
        self.assertIn('OFFICIAL_FDROID_UNNECESSARY_NOTIFICATION_PERMISSION_DENIED_ON_DISPOSABLE_EMULATOR',sh)
        self.assertIn('request_count',sh)
        self.assertIn('"actual_fdroid_client_app_install_verified":True',sh)
        self.assertIn('"actual_fdroid_client_app_upgrade_verified":True',sh)
        self.assertIn('"official_client_repository_persisted_in_database_verified":True',sh)
        self.assertIn('"official_client_repo_signer_pin_in_database_verified":True',sh)
        self.assertIn('db_proof["real_official_client_repo_host_saved_in_native_sqlite"] is True',sh)
        self.assertIn('db_proof["source_sha"]==state["source_sha"]',sh)
        self.assertIn('db_proof["signature_fingerprint_persisted_in_client_database_verified"] is True',sh)
        self.assertIn('ACTUAL_FDROID_CLIENT_SIGNED_REPO_NATIVE_DB_CERT_PIN_AND_INCLIENT_V1_TO_V2_APK_INSTALL_UPDATE_VERIFIED',sh)
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
