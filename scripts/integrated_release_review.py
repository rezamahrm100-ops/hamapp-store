#!/usr/bin/env python3
"""Local production-candidate review gate; never approves or publishes.

Requires *both* real OS package/certificate validation and verified GitHub
producer attestation with owner-pinned workflow, commit and release ref. A
positive result still requires malware/permissions, owner review, signer key
custody and real device acceptance. No network access except gh verification.
"""
import argparse
import json
from pathlib import Path

import release_history
import release_review
import review_provenance


class IntegratedReviewError(ValueError):
    pass


def assess(candidate, registry, history, artifact, trusted_workflow, trusted_source_ref,
           signature_runner=None, gh_runner=None):
    signature_options = {} if signature_runner is None else {"runner": signature_runner}
    source_options = {} if gh_runner is None else {"runner": gh_runner}
    signed = release_review.prepare_review(candidate, registry, history, artifact,
                                           **signature_options)
    verified = review_provenance.verify(
        candidate, registry, artifact, trusted_workflow, trusted_source_ref, **source_options)
    sign = signed["candidate_verification"]
    release = signed["candidate_release"]
    if (not sign["signature_verified"] or not verified["gh_attestation_cryptographically_verified"]
            or verified["artifact_sha256"] != release["artifact_sha256"]
            or sign["sha256"] != verified["artifact_sha256"]
            or verified["source_sha"] != candidate["source_sha"]
            or sign["signer_certificate_sha256"] != release["certificate_sha256"]
            or release["source_repo"] != candidate["source_repo"]):
        raise IntegratedReviewError("source, signer, package or bytes do not agree")
    return {
        "schema_version": 1,
        "release": release,
        "signature": sign,
        "verified_provenance": verified,
        "hash_signature_and_github_source_integrated": True,
        "malware_permission_scan_verified": False,
        "owner_promotion_approved": False,
        "signed_index_and_backup_verified": False,
        "device_install_upgrade_verified": False,
        "catalogue_modified": False,
        "public_distribution_authorized": False,
    }


def main():
    p = argparse.ArgumentParser(description="Actual provenance + package signature preflight (NO RELEASE)")
    p.add_argument("--candidate", required=True, type=Path)
    p.add_argument("--artifact", required=True, type=Path)
    p.add_argument("--registry", type=Path, default=Path(__file__).resolve().parents[1] / "catalog/trusted_signers.json")
    p.add_argument("--history", type=Path, default=Path(__file__).resolve().parents[1] / "catalog/release_history.json")
    p.add_argument("--trusted-workflow", required=True)
    p.add_argument("--trusted-source-ref", required=True)
    p.add_argument("--receipt", required=True, type=Path)
    a = p.parse_args()
    try:
        if a.receipt.is_symlink() or a.receipt.exists():
            raise IntegratedReviewError("refusing to overwrite existing review receipt")
        candidate = json.loads(a.candidate.read_text(encoding="utf-8"))
        registry = json.loads(a.registry.read_text(encoding="utf-8"))
        history = release_history.load_history(a.history)
        result = assess(candidate, registry, history, a.artifact, a.trusted_workflow,
                        a.trusted_source_ref)
        a.receipt.parent.mkdir(parents=True, exist_ok=True)
        with a.receipt.open("x", encoding="utf-8") as out:
            json.dump(result, out, ensure_ascii=False, sort_keys=True, indent=2)
            out.write("\n")
    except (OSError, TypeError, KeyError, ValueError, UnicodeError) as exc:
        p.exit(1, "INTEGRATED_RELEASE_REJECTED: " + str(exc) + "\n")
    print("SIGNED_BINARY_AND_GITHUB_ORIGIN_VERIFIED; OWNER_REVIEW_REQUIRED")


if __name__ == "__main__":
    main()
