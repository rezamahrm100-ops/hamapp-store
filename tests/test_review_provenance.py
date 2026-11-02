import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import review_provenance


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.artifact = Path(self.tmp.name) / "app.apk"
        self.artifact.write_bytes(b"synthetic fixture, not a signed APK")
        self.digest = hashlib.sha256(self.artifact.read_bytes()).hexdigest()
        self.commit = "a" * 40
        self.workflow = "rezamahrm100-ops/demo-project/.github/workflows/release.yml"
        self.candidate = {
            "source_repo": "demo-project", "source_sha": self.commit,
            "package_id": "ir.hamapp.demo", "version_code": 7,
            "release": {
                "app_id": "demo", "platform": "android", "version": "1.2.3",
                "asset_url": "https://github.com/rezamahrm100-ops/demo-project/releases/download/v1.2.3/app.apk",
                "sha256": self.digest, "size_bytes": self.artifact.stat().st_size
            }
        }
        self.registry = {"schema_version": 1, "publishers": [{
            "app_id": "demo", "source_repo": "demo-project",
            "platform": "android", "certificate_sha256": "b" * 64,
            "package_id": "ir.hamapp.demo"
        }]}
        self.verified = [{
            "verificationResult": {"statement": {
                "predicateType": "https://slsa.dev/provenance/v1",
                "subject": [{"name": "app.apk", "digest": {"sha256": self.digest}}]
            }}
        }]
        self.runner = Mock(return_value=SimpleNamespace(returncode=0, stdout=json.dumps(self.verified)))

    def call(self):
        return review_provenance.verify(
            self.candidate, self.registry, self.artifact, self.workflow,
            "refs/tags/v1.2.3", runner=self.runner)

    def test_success_invokes_real_gh_with_identity_pins_and_no_approval(self):
        result = self.call()
        self.assertTrue(result["gh_attestation_cryptographically_verified"])
        self.assertFalse(result["public_distribution_authorized"])
        command = self.runner.call_args.args[0]
        for item in ("--source-digest", self.commit, "--deny-self-hosted-runners",
                     "--signer-workflow", self.workflow, "--source-ref", "refs/tags/v1.2.3"):
            self.assertIn(item, command)

    def test_changed_bytes_rejected_before_running_gh(self):
        self.artifact.write_bytes(b"tampered")
        with self.assertRaises(ValueError):
            self.call()
        self.runner.assert_not_called()

    def test_unapproved_workflow_rejected_before_running_gh(self):
        self.workflow = "attacker/repo/.github/workflows/release.yml"
        with self.assertRaises(ValueError):
            self.call()
        self.runner.assert_not_called()

    def test_unmatched_ref_rejected(self):
        with self.assertRaises(ValueError):
            review_provenance.verify(self.candidate, self.registry, self.artifact, self.workflow, "refs/heads/main", runner=self.runner)

    def test_failed_cli_rejected(self):
        self.runner.return_value.returncode = 1
        with self.assertRaises(ValueError):
            self.call()

    def test_spoofed_json_not_accepted_if_subject_digest_differs(self):
        self.verified[0]["verificationResult"]["statement"]["subject"][0]["digest"]["sha256"] = "f" * 64
        self.runner.return_value.stdout = json.dumps(self.verified)
        with self.assertRaises(ValueError):
            self.call()

    def test_empty_json_and_non_slsa_rejected(self):
        for response in ("[]", '[{"verificationResult":{"statement":{"predicateType":"untrusted"}}}]'):
            self.runner.return_value.stdout = response
            with self.assertRaises(ValueError):
                self.call()

    def test_no_overwrite_receipts_allowed(self):
        text = (ROOT / "scripts/review_provenance.py").read_text()
        self.assertIn('args.receipt.exists() or args.receipt.is_symlink()', text)


if __name__ == "__main__":
    unittest.main()
