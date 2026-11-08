"""Post-install connection controls must work without editing source or relaxing trust."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from windows_client import publisher_connection as conn

class OwnerSetupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="hamapp-owner-setup-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.ca = self.root / "ca.pem"
        self.ca.write_text("PUBLIC CA TEST ONLY", encoding="ascii")
        self.details = {
            "publisher": "sample-publisher",
            "origin": "https://owner.example.org:8443",
            "trusted_ca": str(self.ca),
            "server_cert_sha256": "c" * 64
        }

    def test_strict_https_and_pin_only(self):
        self.assertEqual(conn.validate_profile(self.details)["publisher"], "sample-publisher")
        for field, value in (
            ("origin", "http://owner.example.org"),
            ("origin", "https://user:password@owner.example.org"),
            ("origin", "https://owner.example.org/v1/submissions"),
            ("origin", "https://owner.example.org?access_token=xyz"),
            ("publisher", "repo;echo hello"),
            ("server_cert_sha256", "a" * 63),
            ("trusted_ca", str(self.root / "nonexistent.pem"))):
            with self.subTest(field=field, value=value):
                item = dict(self.details, **{field: value})
                with self.assertRaises(conn.ConfigurationError):
                    conn.validate_profile(item)

    def test_token_is_not_accepted_as_inline_url_or_short_secret(self):
        with self.assertRaises(conn.ConfigurationError):
            conn.valid_token("personal-access-token")
        with self.assertRaises(conn.ConfigurationError):
            conn.valid_token("X" * 64 + "\n")
        self.assertEqual(conn.valid_token("T" * 80), "T" * 80)

    def test_candidate_hash_size_and_source_guard_before_upload(self):
        artifact = self.root / "program.exe"
        data = b"TEST-ONLY-CANDIDATE-NOT-EXECUTABLE"
        artifact.write_bytes(data)
        manifest = {
            "release": {
                "app_id": "program",
                "platform": "windows",
                "version": "1.2.3",
                "asset_url": "https://github.com/rezamahrm100-ops/sample-publisher/releases/download/v1.2.3/program.exe",
                "sha256": hashlib.sha256(data).hexdigest(),
                "size_bytes": len(data)
            },
            "source_repo": "sample-publisher",
            "source_sha": "b" * 40,
            "package_id": None,
            "version_code": None
        }
        candidate = self.root / "candidate.json"
        candidate.write_text(json.dumps(manifest), encoding="utf-8")
        raw, release = conn.validate_candidate(candidate, artifact, "sample-publisher")
        self.assertEqual(release["size_bytes"], len(data))
        self.assertEqual(json.loads(raw)["source_repo"], "sample-publisher")
        with self.assertRaises(conn.ConfigurationError):
            conn.validate_candidate(candidate, artifact, "wrong-publisher")
        artifact.write_bytes(data + b"changed")
        with self.assertRaises(conn.ConfigurationError):
            conn.validate_candidate(candidate, artifact, "sample-publisher")

    @unittest.skipUnless(sys.platform == "win32", "real Windows DPAPI only")
    def test_real_dpapi_save_read_retain_delete_without_plaintext(self):
        p = self.root / "publisher-connection.json"
        token = "s" * 80
        conn.save_profile(self.details, token, path=p)
        self.assertNotIn(token, p.read_text(encoding="utf-8"))
        self.assertEqual(conn.read_profile(path=p)["details"]["publisher"], "sample-publisher")
        cipher1 = conn.read_profile(path=p)["encrypted_token"]
        conn.save_profile(self.details, path=p)
        self.assertEqual(conn.read_profile(path=p)["encrypted_token"], cipher1)
        conn.remove_profile(path=p)
        self.assertFalse(p.exists())

    def test_android_ui_has_distinct_personal_repo_config_and_owner_approval(self):
        java = ROOT / "android/app/src/main/java/ir/hamapp/store"
        ui = (java / "UserRepoSettings.java").read_text(encoding="utf-8")
        main = (java / "MainActivity.java").read_text(encoding="utf-8")
        engine = (java / "InternalFdroidStore.java").read_text(encoding="utf-8")
        self.assertIn("SharedPreferences", ui)
        self.assertIn("RepoPolicy.isAllowed", ui)
        self.assertIn("InternalFdroidStore.openSubscribed", ui)
        self.assertIn("UserRepoSettings.show(this)", main)
        self.assertIn("UserRepoSettings.openSaved(this", main)
        self.assertIn("Source.personal(url, fingerprint)", engine)
        self.assertIn("EntryVerifier", engine)
        self.assertNotIn("private_key", ui)
        self.assertNotIn("API_TOKEN", ui)

    def test_windows_native_gui_reaches_real_secure_connection_actions(self):
        gui = (ROOT / "windows_client/gui.py").read_text(encoding="utf-8")
        ui = (ROOT / "windows_client/owner_setup_ui.py").read_text(encoding="utf-8")
        self.assertIn("open_setup(root)", gui)
        self.assertIn("connection.save_profile(", ui)
        self.assertIn("connection.probe(", ui)
        self.assertIn("connection.submit(", ui)
        self.assertIn("connection.remove_profile(", ui)
        self.assertNotIn("shell=True", ui)

if __name__ == "__main__":
    unittest.main()
