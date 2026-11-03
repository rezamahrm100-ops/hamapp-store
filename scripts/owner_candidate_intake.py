#!/usr/bin/env python3
"""Owner-operated pre-publication binary review, not publisher account login.

Requires independently registered developer signer, valid local binary signature
and GitHub signed producer provenance, then inspects actual archive bytes and
the reviewed Android manifest permission policy. Writes only a proposed review
receipt outside the public repository; no release/registration/publish action.
"""
import argparse
import hashlib
import json
from pathlib import Path

import android_permission_review
import antivirus_binary_review
import binary_archive_review
import release_governance
import release_history
import private_publisher_inbox

ROOT = Path(__file__).resolve().parents[1]

class IntakeError(ValueError):
    pass

def assess(candidate, registry, history, artifact, workflow, ref, *,
           permission_policy=None, aapt="aapt", signature_runner=None,
           gh_runner=None, aapt_runner=None,
           antivirus_scanner=None, antivirus_runner=None):
    base = release_governance.plan_promotion(
        candidate, registry, history, artifact, workflow, ref,
        signature_runner=signature_runner, gh_runner=gh_runner)
    release = candidate["release"]
    full_path = Path(artifact)
    actual_sha = base["verified_artifact_sha256"]
    if actual_sha != release["sha256"]:
        raise IntakeError("verified provenance differs from claimed artifact digest")
    archive_result = None
    if full_path.suffix.lower() in binary_archive_review.SUPPORTED:
        archive_result = binary_archive_review.review(full_path)
        if archive_result["artifact_sha256"] != actual_sha:
            raise IntakeError("archive bytes changed after cryptographic review")
    permission_result = None
    if release["platform"] == "android":
        if permission_policy is None:
            raise IntakeError("independently reviewed Android manifest permissions required")
        options = {} if aapt_runner is None else {"runner": aapt_runner}
        permission_result = android_permission_review.review(
            full_path, permission_policy, aapt=aapt, **options)
        if (permission_result["apk_sha256"] != actual_sha
                or permission_result["package_id"] != candidate["package_id"]
                or permission_result["version_code"] != candidate["version_code"]
                or permission_result["version_name"] != release["version"]):
            raise IntakeError("Android permission review not for exact candidate bytes/identity")
    elif permission_policy is not None:
        raise IntakeError("Android permission policy does not apply to Windows artifacts")
    if (archive_result is None and release["platform"] == "android"):
        raise IntakeError("Android archive structural check required")
    antivirus_result = None
    if antivirus_scanner is not None:
        opts = {} if antivirus_runner is None else {"runner": antivirus_runner}
        antivirus_result = antivirus_binary_review.scan(
            full_path, scanner=antivirus_scanner, **opts)
        if antivirus_result["artifact_sha256"] != actual_sha:
            raise IntakeError("antivirus receipt does not match approved candidate bytes")
    # Final re-hash prevents a local attacker from replacing the candidate after
    # OS+upstream+archive+Android permission checks. Never claim this prevents
    # malicious writes AFTER the review; owner controls artifact custody.
    final_sha, final_bytes = binary_archive_review.file_hash(full_path)
    if final_sha != actual_sha or final_bytes != release["size_bytes"]:
        raise IntakeError("candidate binary changed during review")
    return {
        "schema_version": 1,
        "action": "private_owner_candidate_review",
        "candidate_release": base["candidate_release"],
        "source_sha": candidate["source_sha"],
        "trusted_workflow": workflow,
        "trusted_source_ref": ref,
        "verified_artifact_sha256": actual_sha,
        "public_registry_sha256_before": release_governance.digest(registry),
        "public_history_sha256_before": release_governance.digest(history),
        "actual_archive": archive_result,
        "actual_android_permissions": permission_result,
        "actual_antivirus_signature_scan": antivirus_result,
        "developer_signature_and_github_provenance_checked": True,
        "malware_signature_and_behavior_clearance": False,
        "license_and_privacy_review_complete": False,
        "owner_authentication_via_branch_ruleset_verified": False,
        "signed_repository_and_device_qa_complete": False,
        "owner_promotion_approved": False,
        "public_distribution_authorized": False,
        "files_committed": False,
        "public_catalogue_modified": False
    }

def main():
    p = argparse.ArgumentParser(description="Owner-local actual candidate preflight, no publication")
    p.add_argument("--candidate", type=Path)
    p.add_argument("--artifact", type=Path)
    p.add_argument("--private-inbox-root", type=Path)
    p.add_argument("--submission-id")
    p.add_argument("--publisher-registry", type=Path,
                   default=ROOT / "catalog/trusted_signers.json")
    p.add_argument("--release-history", type=Path,
                   default=ROOT / "catalog/release_history.json")
    p.add_argument("--android-permissions-policy", type=Path)
    p.add_argument("--aapt", default="aapt")
    p.add_argument("--antivirus-scanner", default="clamscan")
    p.add_argument("--trusted-workflow", required=True)
    p.add_argument("--trusted-source-ref", required=True)
    p.add_argument("--output-dir", required=True, type=Path)
    a = p.parse_args()
    try:
        output = a.output_dir
        path = output.resolve()
        if (output.is_symlink() or output.exists()
                or path == ROOT or ROOT in path.parents):
            raise IntakeError("output must be a new directory outside public source checkout")
        if a.private_inbox_root is not None or a.submission_id is not None:
            if (a.private_inbox_root is None or a.submission_id is None
                    or a.candidate is not None or a.artifact is not None):
                raise IntakeError("provide exact private inbox reference OR candidate/artifact")
            candidate, artifact, untrusted_submission = private_publisher_inbox.load_for_preflight(
                a.private_inbox_root, a.submission_id)
        else:
            if a.candidate is None or a.artifact is None:
                raise IntakeError("candidate and artifact required without private inbox")
            candidate = json.loads(a.candidate.read_text(encoding="utf-8"))
            artifact = a.artifact
            untrusted_submission = None
        registry = json.loads(a.publisher_registry.read_text(encoding="utf-8"))
        history = release_history.load_history(a.release_history)
        policy = (json.loads(a.android_permissions_policy.read_text(encoding="utf-8"))
                  if a.android_permissions_policy else None)
        receipt = assess(candidate, registry, history, artifact,
                         a.trusted_workflow, a.trusted_source_ref,
                         permission_policy=policy, aapt=a.aapt,
                         antivirus_scanner=a.antivirus_scanner)
        if untrusted_submission is not None:
            receipt["private_quarantine_submission_id"] = untrusted_submission["submission_id"]
            receipt["publisher_authentication_from_quarantine"] = False
        output.mkdir(parents=True, exist_ok=False)
        with (output / "review-only-receipt.json").open("x", encoding="utf-8") as stream:
            json.dump(receipt, stream, ensure_ascii=False, sort_keys=True, indent=2)
            stream.write("\n")
    except (OSError, ValueError, TypeError, KeyError, UnicodeError) as exc:
        p.exit(1, "PRIVATE_CANDIDATE_REVIEW_REJECTED: " + str(exc) + "\n")
    print("REAL_BINARY_CROSS_CHECKS_PASSED; OWNER_AND_MALWARE_REVIEW_PENDING; NO_RELEASE")

if __name__ == "__main__":
    main()
