"""Private review integration tests. Synthetic fixtures NEVER authorize a release."""
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import owner_verified_release_pipeline as pipe
import private_publisher_inbox as inbox

PIN = "A" * 64
SOURCE = "a" * 40
ID = "e" * 32


@unittest.skipUnless(os.name == "posix", "private publisher service requires POSIX owner modes")
class PrivateEndToEndReview(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.quarantine = inbox.init_root(self.root / "quarantine")
        self.results = self.root / "owner-reviews"
        self.results.mkdir(mode=0o700)
        self.workspace = self.root / "signed-repository"
        self.workspace.mkdir(mode=0o700)
        config = self.workspace / "config.yml"
        inbox._write_private(config, b"repo_keyalias: test-fixture-no-private-key\n")
        self.binary = self.root / "candidate.apk"
        with zipfile.ZipFile(self.binary, "w", zipfile.ZIP_DEFLATED) as zipped:
            zipped.writestr("AndroidManifest.xml", b"fixture-no-actual-Android-binary")
        sha = hashlib.sha256(self.binary.read_bytes()).hexdigest()
        self.candidate = {
            "source_repo": "test-publisher",
            "source_sha": SOURCE,
            "package_id": "ir.hamapp.fixture",
            "version_code": 12,
            "release": {
                "app_id": "example", "platform": "android", "version": "1.2.3",
                "asset_url": "https://github.com/rezamahrm100-ops/test-publisher/releases/download/v1.2.3/candidate.apk",
                "sha256": sha, "size_bytes": self.binary.stat().st_size,
            },
        }
        self.registry = {
            "schema_version": 1, "publishers": [{
                "app_id": "example", "source_repo": "test-publisher",
                "platform": "android", "package_id": "ir.hamapp.fixture",
                "certificate_sha256": "b" * 64,
            }],
        }
        self.history = {"schema_version": 1, "releases": [], "revoked_signers": []}
        self.policy = {"fixture": "not used in synthetic stub"}
        inbox.stage(self.quarantine, self.candidate, self.binary, "test-publisher",
                    make_id=lambda size: ID)

    def run_pipeline(self, stage=None, output=None):
        return pipe.prepare(
            self.quarantine, ID, self.workspace, self.registry, self.history,
            self.policy,
            "rezamahrm100-ops/test-publisher/.github/workflows/release.yml",
            "refs/tags/v1.2.3", PIN,
            output or self.results / "review-01", stage_fn=stage)

    def stub(self, candidate, registry, binary, workspace, **kwargs):
        self.assertEqual(kwargs["antivirus_scanner"], "clamscan")
        self.assertEqual(kwargs["expected_repo_fingerprint"], PIN)
        self.assertEqual(kwargs["trusted_source_ref"], "refs/tags/v1.2.3")
        self.assertEqual(binary.read_bytes(), self.binary.read_bytes())
        return {
            "signed_source_and_signer_verified": True,
            "archive_and_permission_checks_verified": True,
            "fresh_antivirus_signature_scan_verified": True,
            "private_index_v2_signature_and_exact_apk_verified": True,
            "deployed": False, "owner_approved_for_public_distribution": False,
            "sha256": candidate["release"]["sha256"],
            "owner_repo_fingerprint_pinned_input": PIN,
            "public_https_repository_verified": False,
            "f_droid_signed_repository_independently_verified": False,
        }

    def test_quarantine_only_after_review_request_and_never_publicizes(self):
        with self.assertRaises(inbox.QuarantineError):
            self.run_pipeline(self.stub)
        self.assertFalse((self.results / "review-01").exists())
        inbox.transition(self.quarantine, ID, "request_review")
        receipt = self.run_pipeline(self.stub)
        actual = json.loads((self.results / "review-01/private-review.json").read_text())
        self.assertEqual(actual, receipt)
        self.assertEqual(actual["artifact_sha256"], self.candidate["release"]["sha256"])
        self.assertEqual(actual["private_event_count"], 2)
        self.assertFalse(actual["actual_toolchain_required"])  # TEST INJECTION!
        for key in ("owner_promotion_approved", "production_distribution_authorized",
                    "public_catalogue_modified", "public_signed_index_deployed",
                    "owner_device_install_tested"):
            self.assertIs(actual[key], False)
        self.assertEqual(stat.S_IMODE((self.results/"review-01").stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE((self.results/"review-01/private-review.json").stat().st_mode), 0o600)
        self.assertFalse((ROOT / "catalog/apps.json").read_text().count(self.candidate["release"]["sha256"]))

    def test_concurrent_hold_and_rejection_forbidden_during_real_lock(self):
        inbox.transition(self.quarantine, ID, "request_review")
        with inbox.review_lock(self.quarantine, ID):
            for event in ("hold", "reject", "request_review"):
                with self.subTest(event=event), self.assertRaises(inbox.QuarantineError):
                    inbox.transition(self.quarantine, ID, event)
        self.assertEqual(inbox.verify_events(self.quarantine / ID)[0], "review_requested")
        inbox.transition(self.quarantine, ID, "hold")
        self.assertEqual(inbox.verify_events(self.quarantine / ID)[0], "held")

    def test_rejected_or_tampered_quarantine_never_stages(self):
        inbox.transition(self.quarantine, ID, "reject")
        with self.assertRaises(inbox.QuarantineError):
            self.run_pipeline(self.stub)
        self.assertFalse((self.results / "review-01").exists())

    def test_stage_result_cannot_claim_public_approval(self):
        inbox.transition(self.quarantine, ID, "request_review")
        def adversarial(*args, **kwargs):
            result = self.stub(*args, **kwargs)
            result["owner_approved_for_public_distribution"] = True
            return result
        with self.assertRaises(pipe.PrivatePipelineError):
            self.run_pipeline(adversarial)
        self.assertFalse((self.results / "review-01").exists())
        lock = self.workspace / "PUBLISHING_LOCKED_UNTIL_OWNER_REVIEW"
        self.assertTrue(lock.is_file())
        self.assertEqual(stat.S_IMODE(lock.stat().st_mode), 0o600)

    def test_corrupt_signer_and_output_path_fail_before_staging(self):
        inbox.transition(self.quarantine, ID, "request_review")
        with self.assertRaises(ValueError):
            pipe.prepare(self.quarantine, ID, self.workspace, self.registry,
                         self.history, self.policy, "workflow", "tag",
                         "invalid-key", self.results / "bad", stage_fn=self.stub)
        self.assertFalse((self.results / "bad").exists())
        with self.assertRaises(pipe.PrivatePipelineError):
            self.run_pipeline(self.stub, output=ROOT / "catalog/unsafe-review")
        self.assertFalse((ROOT / "catalog/unsafe-review").exists())

    def test_tamper_after_ingest_fails_before_crypto_and_index_update(self):
        inbox.transition(self.quarantine, ID, "request_review")
        (self.quarantine / ID / "candidate.apk").write_bytes(b"tampered")
        invoked = []
        def fake(*args, **kwargs):
            invoked.append(True)
            return self.stub(*args, **kwargs)
        with self.assertRaises(ValueError):
            self.run_pipeline(fake)
        self.assertEqual(invoked, [])
        self.assertFalse((self.results / "review-01").exists())


if __name__ == "__main__":
    unittest.main()
