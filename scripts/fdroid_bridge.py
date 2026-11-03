#!/usr/bin/env python3
"""Owner-local F-Droid APK stage: STRICT signed-source + fresh AV preflight.

Only an actual independently pinned package signer, GitHub producer
attestation, APK manifest permissions, byte-safe archive and current ClamAV
scan can reach 'fdroid update'. This DOES NOT sign a production public
repository, approve a release or deploy any website. No key creation/upload.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys

import android_permission_review
import owner_candidate_intake
import publisher_gate
import release_history
import release_integrity
import review_provenance


class FdroidStageError(publisher_gate.PublisherError):
    pass


def _private_workspace(workspace, apk):
    root = Path(__file__).resolve().parents[1]
    workspace = Path(workspace)
    if workspace.is_symlink() or not workspace.is_dir():
        raise FdroidStageError("existing non-symlink private F-Droid workspace required")
    resolved = workspace.resolve(strict=True)
    if resolved == root or root in resolved.parents or resolved in root.parents:
        raise FdroidStageError("signing workspace must be separate from public source checkout")
    if os.name != "posix":
        raise FdroidStageError("F-Droid signing workspace requires POSIX owner permissions")
    mode = resolved.stat()
    if not stat.S_ISDIR(mode.st_mode) or mode.st_uid != os.geteuid() or (mode.st_mode & 0o077):
        raise FdroidStageError("private F-Droid workspace must be owner-owned and mode 0700")
    config = resolved / "config.yml"
    if config.is_symlink() or not config.is_file() or config.stat().st_mode & 0o077:
        raise FdroidStageError("existing private config.yml (0600) required")
    repo = resolved / "repo"
    if repo.is_symlink() or (repo.exists() and not repo.is_dir()):
        raise FdroidStageError("F-Droid repo directory cannot be symlink or file")
    if repo.exists() and repo.stat().st_mode & 0o077:
        raise FdroidStageError("F-Droid repository directory must be private")
    dest = repo / Path(apk).name
    if (Path(apk).is_symlink() or Path(apk).suffix.lower() != ".apk"
            or dest.exists() or dest.is_symlink()):
        raise FdroidStageError("expected a unique non-symlink APK filename")
    return resolved, repo, dest


def stage(candidate, registry, apk, workspace, *,
          trusted_workflow=None, trusted_source_ref=None, permission_policy=None,
          runner=None, gh_runner=None, aapt_runner=None, antivirus_runner=None,
          antivirus_scanner="clamscan", update_runner=subprocess.run, history=None):
    """Stage strictly after actual independent review (never merely a JSON flag).

    Runners are injectable for isolated unit tests only. Real command-line
    execution supplies no injected verifier and ALWAYS requires actual tools.
    """
    if history is None:
        history = release_history.load_history(
            Path(__file__).resolve().parents[1] / "catalog/release_history.json")
    release_history.check_continuity(candidate, registry, history)
    if candidate["release"]["platform"] != "android":
        raise FdroidStageError("only real Android APK candidates may enter F-Droid")
    resolved, repo, dest = _private_workspace(workspace, apk)
    if (not isinstance(trusted_workflow, str)
            or not review_provenance.WORKFLOW.fullmatch(trusted_workflow)
            or not isinstance(trusted_source_ref, str)
            or not review_provenance.REF.fullmatch(trusted_source_ref)):
        raise FdroidStageError("independently approved GitHub release workflow and immutable tag required")
    if not isinstance(permission_policy, dict):
        raise FdroidStageError("independently approved Android manifest permission policy required")
    android_permission_review.validate_policy(permission_policy)
    if not isinstance(antivirus_scanner, str) or not antivirus_scanner.strip():
        raise FdroidStageError("actual fresh ClamAV scanner required; cannot disable")
    opts = {"permission_policy": permission_policy, "antivirus_scanner": antivirus_scanner}
    if runner is not None:
        opts["signature_runner"] = runner
    if gh_runner is not None:
        opts["gh_runner"] = gh_runner
    if aapt_runner is not None:
        opts["aapt_runner"] = aapt_runner
    if antivirus_runner is not None:
        opts["antivirus_runner"] = antivirus_runner

    # This invokes actual independently registered signer + GitHub crypto
    # provenance + archive CRC/ZIP safety + aapt permission + fresh clamscan.
    result = owner_candidate_intake.assess(
        candidate, registry, history, apk,
        trusted_workflow, trusted_source_ref, **opts)
    scanner = result.get("actual_antivirus_signature_scan")
    if (result.get("developer_signature_and_github_provenance_checked") is not True
            or result.get("verified_artifact_sha256") != candidate["release"]["sha256"]
            or not isinstance(scanner, dict)
            or scanner.get("actual_signature_scan_completed_without_detection") is not True
            or scanner.get("artifact_sha256") != candidate["release"]["sha256"]
            or not isinstance(result.get("actual_android_permissions"), dict)
            or result["actual_android_permissions"].get("requested_permissions_allowlist_checked") is not True
            or not isinstance(result.get("actual_archive"), dict)
            or result["actual_archive"].get("actual_archive_crc_and_paths_checked") is not True):
        raise FdroidStageError("actual signer/provenance/archive/permission/antivirus verification incomplete")
    if result.get("public_distribution_authorized") is not False:
        raise FdroidStageError("unexpected publication-authorization flag in preflight")

    repo.mkdir(mode=0o700, exist_ok=True)
    try:
        with dest.open("xb") as output, Path(apk).open("rb") as source:
            shutil.copyfileobj(source, output, length=1024 * 1024)
            output.flush()
            os.fsync(output.fileno())
        os.chmod(dest, 0o600)
        # Recheck BOTH source and copied bytes immediately before invoking
        # official fdroid tooling. No user-provided success receipt is trusted.
        release_integrity.verify_file(candidate["release"], dest)
        release_integrity.verify_file(candidate["release"], apk)
        done = update_runner(["fdroid", "update", "--create-metadata"],
                             cwd=str(resolved), capture_output=True, text=True,
                             timeout=300, check=False)
        if done.returncode != 0:
            raise FdroidStageError("upstream fdroid update failed; check private workspace logs")
        release_integrity.verify_file(candidate["release"], dest)
    except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
        dest.unlink(missing_ok=True)
        raise FdroidStageError("verified F-Droid staging failed and new APK was removed") from exc
    return {
        "schema_version": 1, "staged_filename": dest.name,
        "sha256": candidate["release"]["sha256"],
        "signed_source_and_signer_verified": True,
        "archive_and_permission_checks_verified": True,
        "fresh_antivirus_signature_scan_verified": True,
        "f_droid_signed_repository_independently_verified": False,
        "owner_approved_for_public_distribution": False,
        "deployed": False, "review_required": True
    }


def main():
    p = argparse.ArgumentParser(description="Stage only actually verified Android package; NEVER DEPLOY")
    p.add_argument("--candidate", type=Path, required=True)
    p.add_argument("--artifact", type=Path, required=True)
    p.add_argument("--workspace", type=Path, required=True)
    p.add_argument("--registry", type=Path, default=Path(__file__).resolve().parents[1] / "catalog/trusted_signers.json")
    p.add_argument("--history", type=Path, default=Path(__file__).resolve().parents[1] / "catalog/release_history.json")
    p.add_argument("--trusted-workflow", required=True)
    p.add_argument("--trusted-source-ref", required=True)
    p.add_argument("--android-permissions-policy", type=Path, required=True)
    p.add_argument("--antivirus-scanner", default="clamscan")
    p.add_argument("--receipt", type=Path, required=True)
    a = p.parse_args()
    try:
        if a.receipt.exists() or a.receipt.is_symlink():
            raise FdroidStageError("receipt already exists")
        candidate = json.loads(a.candidate.read_text(encoding="utf-8"))
        registry = json.loads(a.registry.read_text(encoding="utf-8"))
        policy = json.loads(a.android_permissions_policy.read_text(encoding="utf-8"))
        receipt = stage(candidate, registry, a.artifact, a.workspace,
                        trusted_workflow=a.trusted_workflow,
                        trusted_source_ref=a.trusted_source_ref,
                        permission_policy=policy, antivirus_scanner=a.antivirus_scanner,
                        history=release_history.load_history(a.history))
        a.receipt.parent.mkdir(parents=True, exist_ok=True)
        with a.receipt.open("x", encoding="utf-8") as out:
            json.dump(receipt, out, indent=2, sort_keys=True)
            out.write("\n")
    except (OSError, ValueError, TypeError, KeyError) as e:
        p.exit(1, "FDROID_VERIFY_AND_STAGE_REJECTED: " + str(e) + "\n")
    print("VERIFIED_PRIVATE_FDROID_STAGE_ONLY; SIGNED_INDEX_AND_OWNER_DEPLOYMENT_NOT_APPROVED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
