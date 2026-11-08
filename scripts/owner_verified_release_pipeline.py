#!/usr/bin/env python3
"""One owner-private Android pipeline: quarantine -> real crypto/AV -> signed index.

The trusted service's private quarantine is the ONLY binary input; a claimed
publisher ID or a success JSON is never treated as authenticated identity.
Reuse existing upstream fdroidserver verifier and independently registered
APK signing/provenance/permission/ClamAV gates through fdroid_bridge.stage().
No public catalogue, GitHub issue/PR, release or deployment is changed.
"""
import argparse
import json
import os
from pathlib import Path
import stat
import sys

import fdroid_bridge
import private_publisher_inbox as inbox
import release_governance
import release_history
import release_integrity
import verify_fdroid_private_stage

ROOT = Path(__file__).resolve().parents[1]


class PrivatePipelineError(ValueError):
    pass


def _read_document(path, *, maximum=1024 * 1024):
    source = Path(path)
    if (source.is_symlink() or not source.is_file()
            or not 0 < source.stat().st_size <= maximum):
        raise PrivatePipelineError("independently supplied configuration file missing or invalid")
    return json.loads(source.read_text(encoding="utf-8"))


def _private_output_parent(output):
    path = Path(output)
    parent = path.parent
    if path.is_symlink() or path.exists():
        raise PrivatePipelineError("private review output must be new")
    if os.name != "posix":
        raise PrivatePipelineError("private release pipeline requires POSIX owner-only storage")
    folder = inbox._private_dir(parent)
    resolved = path.resolve()
    if (resolved.parent != folder or ROOT == resolved or ROOT in resolved.parents):
        raise PrivatePipelineError("output must be direct child of private owner review directory")
    return path


def _verify_stage_receipt(result, candidate, fingerprint):
    release = candidate["release"]
    required = {
        "signed_source_and_signer_verified": True,
        "archive_and_permission_checks_verified": True,
        "fresh_antivirus_signature_scan_verified": True,
        "private_index_v2_signature_and_exact_apk_verified": True,
        "deployed": False,
        "owner_approved_for_public_distribution": False,
    }
    if not isinstance(result, dict) or any(result.get(k) is not v for k, v in required.items()):
        raise PrivatePipelineError("verified staging has missing or unauthorized evidence")
    if (result.get("sha256") != release["sha256"]
            or result.get("owner_repo_fingerprint_pinned_input") != fingerprint
            or result.get("public_https_repository_verified") is not False
            or result.get("f_droid_signed_repository_independently_verified") is not False):
        raise PrivatePipelineError("staging identity or real-world trust gates mismatch")


def prepare(root, submission_id, workspace, registry, history, policy, workflow,
            source_ref, fingerprint, output, *, stage_fn=None):
    """Stage exactly one review-requested quarantine item and seal private audit.

    Injection is only for synthetic Python unit tests; the real CLI never
    supplies stage_fn and therefore ALWAYS executes actual toolchain gates.
    """
    output = _private_output_parent(output)
    if not isinstance(fingerprint, str):
        raise PrivatePipelineError("independently pinned repository signing key required")
    signer = verify_fdroid_private_stage.checked_sha(fingerprint)
    if stage_fn is None:
        stage_fn = fdroid_bridge.stage
    with inbox.review_lock(root, submission_id) as folder:
        candidate, artifact, receipt = inbox.load_for_preflight(root, submission_id)
        if candidate["release"]["platform"] != "android":
            raise PrivatePipelineError("this private signing route accepts only Android; native Windows Authenticode requires Windows")
        # Require independently reviewed trust documents, not publisher claims
        # or the private inbox's unauthenticated producer label.
        release_history.check_continuity(candidate, registry, history)
        if not isinstance(policy, dict):
            raise PrivatePipelineError("separately reviewed manifest policy required")
        # Check that workspace and target filename are usable before any
        # scanning, signing or permanent F-Droid index modification starts.
        fdroid_bridge._private_workspace(workspace, artifact)
        before = release_governance.digest(history)
        event_state, event_sha, event_count = inbox.verify_events(folder)
        if event_state != "review_requested":
            raise PrivatePipelineError("private submission is not requesting owner review")
        stage_done = False
        try:
            signed = stage_fn(candidate, registry, artifact, workspace,
                              trusted_workflow=workflow, trusted_source_ref=source_ref,
                              permission_policy=policy,
                              antivirus_scanner="clamscan",
                              expected_repo_fingerprint=signer,
                              history=history)
            stage_done = True
            _verify_stage_receipt(signed, candidate, signer)
            # Verify quarantined source bytes *again* after the signed index
            # update; the private lock prevents concurrent hold/rejection.
            _, same_artifact, same_receipt = inbox.load_for_preflight(root, submission_id)
            release_integrity.verify_file(candidate["release"], same_artifact)
            if (same_receipt != receipt or same_artifact != artifact
                    or inbox.verify_events(folder) != (event_state, event_sha, event_count)):
                raise PrivatePipelineError("private review identity/event chain changed")
            audit = {
                "schema_version": 1,
                "action": "owner_private_fdroid_signed_index_preflight",
                "submission_id": submission_id,
                "source_repo_claim": candidate["source_repo"],
                "verified_producer_source_sha": candidate["source_sha"],
                "app_id": candidate["release"]["app_id"],
                "version": candidate["release"]["version"],
                "artifact_sha256": candidate["release"]["sha256"],
                "artifact_size_bytes": candidate["release"]["size_bytes"],
                "package_id": candidate["package_id"],
                "version_code": candidate["version_code"],
                "private_event_count": event_count,
                "private_last_event_sha256": event_sha,
                "trusted_history_sha256": before,
                "reviewed_signer_registry_sha256": release_governance.digest(registry),
                "private_stage": signed,
                "actual_toolchain_required": stage_fn is fdroid_bridge.stage,
                "public_catalogue_modified": False,
                "owner_promotion_approved": False,
                "production_distribution_authorized": False,
                "source_public_released": False,
                "public_signed_index_deployed": False,
                "owner_device_install_tested": False,
            }
            output.mkdir(mode=0o700, parents=False, exist_ok=False)
            try:
                inbox._write_private(output / "private-review.json", inbox._canonical(audit))
            except Exception:
                (output / "private-review.json").unlink(missing_ok=True)
                output.rmdir()
                raise
            return audit
        except Exception:
            if stage_done:
                # The signed index could now differ from its last reviewed
                # state; lock the PRIVATE owner workspace, never roll forward
                # or silently publish an unaudited repo.
                lock = Path(workspace) / "PUBLISHING_LOCKED_UNTIL_OWNER_REVIEW"
                if not lock.exists():
                    inbox._write_private(lock, b"Private staging postflight failed; owner repair required.\n")
            raise


def main():
    parser = argparse.ArgumentParser(description="Private verified publisher intake -> signed local F-Droid stage; NEVER PUBLISH")
    parser.add_argument("--private-inbox-root", type=Path, required=True)
    parser.add_argument("--submission-id", required=True)
    parser.add_argument("--fdroid-workspace", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--android-permissions-policy", type=Path, required=True)
    parser.add_argument("--trusted-workflow", required=True)
    parser.add_argument("--trusted-source-ref", required=True)
    parser.add_argument("--expected-repo-fingerprint", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        registry = _read_document(args.registry)
        history = release_history.validate_history(_read_document(args.history))
        policy = _read_document(args.android_permissions_policy)
        prepare(args.private_inbox_root, args.submission_id,
                args.fdroid_workspace, registry, history, policy,
                args.trusted_workflow, args.trusted_source_ref,
                args.expected_repo_fingerprint, args.output_dir)
    except (OSError, ValueError, TypeError, KeyError, UnicodeError) as exc:
        parser.exit(1, "OWNER_PRIVATE_RELEASE_PREFLIGHT_REJECTED; NO_PUBLICATION: " +
                    str(exc) + "\n")
    print("PRIVATE_SIGNED_INDEX_PREFLIGHT_VERIFIED; NO_PUBLIC_APPROVAL_OR_DEPLOYMENT")


if __name__ == "__main__":
    sys.exit(main())
