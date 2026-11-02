"""Offline checks for fail-closed, owner-reviewed immutable web deployments."""
import sys
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_catalog
import web_release_gate


class WebReleaseGateTests(unittest.TestCase):
    def setUp(self):
        self.sha = "a" * 40
        self.digest = "b" * 64
        self.url = "https://apps.example.org/releases/" + self.sha + "/"
        self.origins = {"schema_version": 1, "origins": [{
            "app_id": "demo-web", "source_repo": "approved-web",
            "origin": "https://apps.example.org"
        }]}
        self.history = {"schema_version": 1, "releases": [{
            "app_id": "demo-web", "version": "1.0.0", "source_repo": "approved-web",
            "source_sha": self.sha, "artifact_sha256": self.digest,
            "deployment_url": self.url, "status": "approved"
        }]}
        self.data = {"schema_version": 1, "apps": [{
            "id": "demo-web", "name_fa": "وب", "name_en": "Web",
            "description": "Approved fixture only", "platforms": ["web"],
            "status": "released", "version": "1.0.0", "download_url": self.url,
            "release_proof": {"source_repo": "approved-web",
                              "source_sha": self.sha, "artifact_sha256": self.digest}
        }]}
        self.binary_origins = {"schema_version": 1, "publishers": []}
        self.binary_history = {"schema_version": 1, "releases": [], "revoked_signers": []}

    def check(self):
        return validate_catalog.validate(
            self.data, self.binary_origins, self.binary_history, self.origins, self.history)

    def test_fixture_is_statically_approved_not_live_verified(self):
        self.assertEqual(self.check(), [])

    def test_empty_real_registries_still_block_release(self):
        self.origins["origins"] = []
        self.history["releases"] = []
        self.assertTrue(self.check())

    def test_host_spoofing_blocked(self):
        self.data["apps"][0]["download_url"] = self.url.replace(
            "apps.example.org", "apps.example.org.attacker.test")
        self.assertTrue(self.check())

    def test_credentials_query_fragment_and_non_https_rejected(self):
        for url in (
            self.url.replace("https://", "http://"),
            self.url.replace("https://", "https://hacker@"),
            self.url + "?redirect=https://evil.test",
            self.url + "#unsafe",
            "https://apps.example.org:443/releases/" + self.sha + "/",
            "https://apps.example.org/releases/../" + self.sha + "/",
        ):
            with self.subTest(url=url):
                copy = deepcopy(self.data)
                copy["apps"][0]["download_url"] = url
                self.assertTrue(validate_catalog.validate(
                    copy, self.binary_origins, self.binary_history, self.origins, self.history))

    def test_changed_deployment_digest_blocked(self):
        self.data["apps"][0]["release_proof"]["artifact_sha256"] = "c" * 64
        self.assertTrue(self.check())

    def test_mismatched_source_commit_blocked(self):
        self.data["apps"][0]["release_proof"]["source_sha"] = "c" * 40
        self.assertTrue(self.check())

    def test_mutable_root_url_blocked(self):
        self.history["releases"][0]["deployment_url"] = "https://apps.example.org/"
        self.assertTrue(self.check())

    def test_latest_revoked_release_blocks_stale_approved_link(self):
        self.history["releases"].append({
            **self.history["releases"][0], "version": "2.0.0",
            "source_sha": "c" * 40, "deployment_url":
                "https://apps.example.org/releases/" + "c" * 40 + "/",
            "status": "revoked"
        })
        self.assertTrue(self.check())

    def test_same_app_repeated_trust_root_blocked(self):
        self.origins["origins"].append(dict(self.origins["origins"][0]))
        self.assertTrue(self.check())

    def test_duplicate_web_version_blocked(self):
        self.history["releases"].append(dict(self.history["releases"][0]))
        self.assertTrue(self.check())

    def test_empty_release_approval_does_not_publish(self):
        self.data["apps"][0]["status"] = "planned"
        self.data["apps"][0]["version"] = None
        self.data["apps"][0]["download_url"] = None
        self.data["apps"][0].pop("release_proof")
        self.assertEqual(self.check(), [])

    def test_trust_files_must_have_exact_schema(self):
        with self.assertRaises(web_release_gate.WebReleaseError):
            web_release_gate.validate_origins({"schema_version": 1, "origins": {}, "allow_all": True})


if __name__ == "__main__":
    unittest.main()
