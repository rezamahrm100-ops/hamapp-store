#!/usr/bin/env python3
"""Run GitHub's actual cryptographic attestation verifier for a candidate binary.

A JSON file or asserted source SHA alone is never accepted. This checks the
artifact bytes, pinned producer workflow, source revision and immutable ref.
Publisher signature and owner authorization are separate gates.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

import publisher_gate
import release_integrity

WORKFLOW = re.compile(r"rezamahrm100-ops/[a-z0-9]+(?:-[a-z0-9]+)*/\.github/workflows/[A-Za-z0-9_-]+\.ya?ml\Z")
REF = re.compile(r"refs/tags/v?[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?\Z")
PREDICATE = "https://slsa.dev/provenance/v1"


class ProvenanceError(ValueError):
    pass


def verify(candidate, artifact, trusted_workflow, trusted_source_ref, runner=subprocess.run):
    """No injected receipts: in production runner executes gh with strict flags."""
    release = publisher_gate.validate_candidate(candidate, {
        "schema_version": 1, "publishers": [{
            "app_id": candidate["release"]["app_id"],
            "platform": candidate["release"]["platform"],
            "source_repo": candidate["source_repo"],
            "package_id": candidate["package_id"],
            # Policy-only input here: true certificate approval is checked separately.
            "certificate_sha256": "0" * 64,
        }]
    })
    del release
    manifest = candidate["release"]
    full_repo = publisher_gate.OWNER + "/" + candidate["source_repo"]
    if not isinstance(trusted_workflow, str) or not WORKFLOW.fullmatch(trusted_workflow):
        raise ProvenanceError("independently approved producer workflow is required")
    if not trusted_workflow.startswith(full_repo + "/.github/workflows/"):
        raise ProvenanceError("workflow does not belong to claimed source repository")
    if (not isinstance(trusted_source_ref, str) or not REF.fullmatch(trusted_source_ref)
            or trusted_source_ref[10:].lstrip("v") != manifest["version"]):
        raise ProvenanceError("independently approved release ref does not match version")
    # This is the actual byte-level hash check, not a claimed digest.
    receipt = release_integrity.verify_file(manifest, artifact)
    command = [
        "gh", "attestation", "verify", str(Path(artifact)), "--repo", full_repo,
        "--signer-workflow", trusted_workflow,
        "--source-ref", trusted_source_ref,
        "--source-digest", candidate["source_sha"],
        "--predicate-type", PREDICATE,
        "--deny-self-hosted-runners", "--format", "json"
    ]
    try:
        outcome = runner(command, capture_output=True, text=True, timeout=180, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ProvenanceError("GitHub cryptographic verifier unavailable or timed out") from exc
    if outcome.returncode != 0 or len(outcome.stdout) > 2_000_000:
        raise ProvenanceError("GitHub attestation verification failed")
    try:
        entries = json.loads(outcome.stdout)
    except (TypeError, ValueError) as exc:
        raise ProvenanceError("invalid verified GitHub response") from exc
    if not isinstance(entries, list) or not entries:
        raise ProvenanceError("no verified attestations")
    found = False
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        verified = entry.get("verificationResult")
        statement = verified.get("statement") if isinstance(verified, dict) else None
        if not isinstance(statement, dict) or statement.get("predicateType") != PREDICATE:
            continue
        for subject in statement.get("subject", []):
            if not isinstance(subject, dict):
                continue
            name = subject.get("name")
            if (isinstance(name, str)
                    and (name == Path(artifact).name or name.endswith("/" + Path(artifact).name))
                    and isinstance(subject.get("digest"), dict)
                    and subject["digest"].get("sha256") == receipt["sha256"]):
                found = True
    if not found:
        raise ProvenanceError("no cryptographically verified subject matches actual artifact bytes")
    return {
        "schema_version": 1, "producer_repo": full_repo,
        "producer_workflow": trusted_workflow, "source_ref": trusted_source_ref,
        "source_sha": candidate["source_sha"], "artifact_sha256": receipt["sha256"],
        "artifact_size_bytes": receipt["size_bytes"],
        "gh_attestation_cryptographically_verified": True,
        "owner_approved": False, "developer_signing_identity_verified": False,
        "malware_clearance_verified": False, "device_upgrade_verified": False,
        "public_distribution_authorized": False
    }


def main():
    parser = argparse.ArgumentParser(description="Verify real GitHub artifact provenance (not release approval)")
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--trusted-workflow", required=True)
    parser.add_argument("--trusted-source-ref", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.receipt.exists() or args.receipt.is_symlink():
            raise ProvenanceError("receipt already exists")
        candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
        result = verify(candidate, args.artifact, args.trusted_workflow, args.trusted_source_ref)
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        with args.receipt.open("x", encoding="utf-8") as out:
            json.dump(result, out, sort_keys=True, indent=2)
            out.write("\n")
    except (OSError, ValueError, TypeError, KeyError) as exc:
        parser.exit(1, "PROVENANCE_REJECTED: " + str(exc) + "\n")
    print("GITHUB_PROVENANCE_VERIFIED; OWNER_AND_PACKAGE_SIGNATURE_REVIEW_REQUIRED")


if __name__ == "__main__":
    main()
