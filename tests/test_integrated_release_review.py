"""Synthetic unit tests: never count mock receipts as release approval."""
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import integrated_release_review


class IntegratedGateTests(unittest.TestCase):
    def setUp(self):
        self.candidate = {"source_repo": "demo", "source_sha": "a" * 40}
        self.history = {"schema_version": 1, "releases": [], "revoked_signers": []}
        self.registry = {"schema_version": 1, "publishers": []}
        self.receipt = {
            "candidate_release": {"artifact_sha256": "b" * 64,
                                  "certificate_sha256": "c" * 64, "source_repo": "demo"},
            "candidate_verification": {"signature_verified": True,
                                       "sha256": "b" * 64,
                                       "signer_certificate_sha256": "c" * 64}
        }
        self.origin = {
            "gh_attestation_cryptographically_verified": True,
            "artifact_sha256": "b" * 64, "source_sha": "a" * 40
        }

    def assess(self):
        return integrated_release_review.assess(
            self.candidate, self.registry, self.history, Path("dummy.apk"),
            "rezamahrm100-ops/demo/.github/workflows/release.yml",
            "refs/tags/v1.0.0"
        )

    def test_requires_both_verified_gates_and_does_not_publish(self):
        with patch.object(integrated_release_review.release_review, "prepare_review", return_value=self.receipt) as sig, \
             patch.object(integrated_release_review.review_provenance, "verify", return_value=self.origin) as prov:
            r = self.assess()
        self.assertTrue(r["hash_signature_and_github_source_integrated"])
        self.assertFalse(r["public_distribution_authorized"])
        self.assertFalse(r["catalogue_modified"])
        self.assertFalse(r["malware_permission_scan_verified"])
        sig.assert_called_once()
        prov.assert_called_once()

    def test_mismatch_is_rejected(self):
        for field, value in (("artifact_sha256", "d" * 64),
                             ("source_sha", "e" * 40),
                             ("gh_attestation_cryptographically_verified", False)):
            with self.subTest(field=field):
                wrong = dict(self.origin, **{field: value})
                with patch.object(integrated_release_review.release_review, "prepare_review", return_value=self.receipt), \
                     patch.object(integrated_release_review.review_provenance, "verify", return_value=wrong):
                    with self.assertRaises(integrated_release_review.IntegratedReviewError):
                        self.assess()

    def test_missing_source_attestation_never_falls_back(self):
        with patch.object(integrated_release_review.release_review, "prepare_review", return_value=self.receipt), \
             patch.object(integrated_release_review.review_provenance, "verify", side_effect=ValueError("no attestation")):
            with self.assertRaises(ValueError):
                self.assess()

    def test_unsigned_candidate_rejected_before_attestation(self):
        with patch.object(integrated_release_review.release_review, "prepare_review", side_effect=ValueError("unsigned")), \
             patch.object(integrated_release_review.review_provenance, "verify") as prov:
            with self.assertRaises(ValueError):
                self.assess()
            prov.assert_not_called()


if __name__ == "__main__":
    unittest.main()
