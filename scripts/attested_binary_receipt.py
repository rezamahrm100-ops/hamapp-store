#!/usr/bin/env python3
"""Record byte-matched GitHub CLI verification for trusted-main review only.

Never pass arbitrary user-supplied JSON as trust evidence: ONLY invoke after
a successful gh attestation verify command with pinned workflow/branch/SHA.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROLES = {"android-debug": "app-debug.apk", "windows-unsigned": "HamApp-Windows-Preview.exe"}
SHA40 = re.compile(r"[0-9a-f]{40}\Z")
PREDICATE = "https://slsa.dev/provenance/v1"


class EvidenceError(ValueError):
    pass


def make_receipt(artifact, cli_result, role, source_sha):
    if role not in ROLES or not SHA40.fullmatch(source_sha):
        raise EvidenceError("unknown role or non-pinned source SHA")
    path = Path(artifact)
    if path.name != ROLES[role] or path.is_symlink() or not path.is_file():
        raise EvidenceError("missing or unexpected artifact")
    sha = hashlib.sha256()
    total = 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            total += len(block)
            if total > 2 * 1024**3:
                raise EvidenceError("oversize binary")
            sha.update(block)
    if not total:
        raise EvidenceError("empty binary")
    if not isinstance(cli_result, list) or not cli_result:
        raise EvidenceError("no verified attestation results")
    matched = False
    for record in cli_result:
        if not isinstance(record, dict):
            continue
        result = record.get("verificationResult")
        statement = result.get("statement") if isinstance(result, dict) else None
        if not isinstance(statement, dict) or statement.get("predicateType") != PREDICATE:
            continue
        subjects = statement.get("subject")
        if not isinstance(subjects, list):
            continue
        for subject in subjects:
            if not isinstance(subject, dict):
                continue
            digest = subject.get("digest")
            subject_name = subject.get("name")
            if (isinstance(digest, dict) and digest.get("sha256") == sha.hexdigest()
                    and isinstance(subject_name, str)
                    and (subject_name == path.name or subject_name.endswith("/" + path.name))):
                matched = True
    if not matched:
        raise EvidenceError("no verified subject matches exact binary SHA-256 and name")
    return {
        "schema_version": 1,
        "source_commit": source_sha,
        "artifact": path.name,
        "sha256": sha.hexdigest(),
        "size_bytes": total,
        "role": role,
        "gh_verification": "required_successful_main_workflow_with_pinned_identity",
        "github_build_provenance_checked": True,
        "android_release_key_verified": False,
        "windows_authenticode_verified": False,
        "fdroid_repo_index_signature_verified": False,
        "owner_approved_for_distribution": False,
        "device_install_upgrade_verified": False,
        "production_ready": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", required=True, type=Path)
    parser.add_argument("--verified-gh-json", required=True, type=Path)
    parser.add_argument("--role", required=True, choices=sorted(ROLES))
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.output.exists() or args.output.is_symlink():
            raise EvidenceError("existing receipt cannot be overwritten")
        verification = json.loads(args.verified_gh_json.read_text(encoding="utf-8"))
        receipt = make_receipt(args.artifact, verification, args.role, args.source_sha)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (ValueError, OSError, UnicodeError) as exc:
        parser.exit(1, "BUILD_PROVENANCE_REJECTED: " + str(exc) + "\n")
    print("GITHUB_BUILD_ATTESTATION_MATCHED; PRODUCTION_SIGNING_NOT_VERIFIED")


if __name__ == "__main__":
    main()
