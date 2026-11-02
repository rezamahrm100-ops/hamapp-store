#!/usr/bin/env python3
"""Fail-closed pre-publish continuity policy for owner-reviewed release history.

No downloading, publishing, signing, or history modification. Not a proof of provenance.
"""
import json
from pathlib import Path
import re
import sys

import publisher_gate
import release_integrity

HEX64 = re.compile(r"[0-9a-f]{64}\Z")
CORE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z.-]+))?$")
STATUS = {"approved", "revoked"}
RECORD_KEYS = {"app_id", "platform", "version", "version_code", "source_repo",
               "package_id", "certificate_sha256", "artifact_sha256", "status"}


class HistoryError(ValueError):
    """Invalid trust history or rollback/replay candidate."""


def semver_key(version):
    if not isinstance(version, str):
        raise HistoryError("version must be a string")
    match = CORE.fullmatch(version)
    if not match:
        raise HistoryError("expected strict three-component SemVer without build metadata")
    major, minor, patch = (int(match.group(i)) for i in (1, 2, 3))
    pre = match.group(4)
    if pre is None:
        return (major, minor, patch, 1, ())
    tokens = pre.split(".")
    if any(not t or (t.isdecimal() and len(t) > 1 and t.startswith("0")) for t in tokens):
        raise HistoryError("invalid prerelease identifiers")
    parts = tuple((0, int(t)) if t.isascii() and t.isdigit() else (1, t) for t in tokens)
    return (major, minor, patch, 0, parts)


def validate_history(history):
    if not isinstance(history, dict) or set(history) != {
        "schema_version", "releases", "revoked_signers"
    } or type(history["schema_version"]) is not int or history["schema_version"] != 1:
        raise HistoryError("invalid history schema")
    if not isinstance(history["releases"], list) or not isinstance(history["revoked_signers"], list):
        raise HistoryError("history releases/revoked_signers must be arrays")
    if len(history["releases"]) > 10000 or len(history["revoked_signers"]) > 10000:
        raise HistoryError("unreasonable history size")
    revoked = history["revoked_signers"]
    if any(not isinstance(fp, str) or not HEX64.fullmatch(fp) for fp in revoked) or len(set(revoked)) != len(revoked):
        raise HistoryError("invalid/duplicate revoked signer")
    versions = set()
    hashes = set()
    for entry in history["releases"]:
        if not isinstance(entry, dict) or set(entry) != RECORD_KEYS:
            raise HistoryError("invalid history entry schema")
        app_id = entry["app_id"]
        platform = entry["platform"]
        if not isinstance(app_id, str) or not release_integrity.ID.fullmatch(app_id):
            raise HistoryError("invalid historical app id")
        if platform not in ("android", "windows"):
            raise HistoryError("invalid historical platform")
        semver_key(entry["version"])
        if not isinstance(entry["source_repo"], str) or not release_integrity.ID.fullmatch(entry["source_repo"]):
            raise HistoryError("invalid historical source")
        if not isinstance(entry["certificate_sha256"], str) or not HEX64.fullmatch(entry["certificate_sha256"]):
            raise HistoryError("invalid historical certificate")
        if not isinstance(entry["artifact_sha256"], str) or not HEX64.fullmatch(entry["artifact_sha256"]):
            raise HistoryError("invalid historical artifact")
        if entry["status"] not in STATUS:
            raise HistoryError("historical entry must be approved or revoked")
        if platform == "android":
            if not isinstance(entry["package_id"], str) or not publisher_gate.PACKAGE.fullmatch(entry["package_id"]):
                raise HistoryError("invalid historical Android identity")
            if type(entry["version_code"]) is not int or not 1 <= entry["version_code"] <= 2**31 - 1:
                raise HistoryError("invalid historical Android versionCode")
        elif entry["package_id"] is not None or entry["version_code"] is not None:
            raise HistoryError("Windows identity fields must be null")
        key = (app_id, platform, entry["version"])
        if key in versions:
            raise HistoryError("duplicate recorded version")
        versions.add(key)
        identity = (app_id, platform, entry["artifact_sha256"])
        if identity in hashes:
            raise HistoryError("reused historical artifact hash")
        hashes.add(identity)
    return history


def check_continuity(candidate, registry, history):
    """Validate candidate against existing, separately reviewed historical commitments.

    This is only a policy PRECHECK; it does not verify the actual binary or
    cryptographic signatures. Call publisher_gate.verify separately.
    """
    publisher = publisher_gate.validate_candidate(candidate, registry)
    validate_history(history)
    release = candidate["release"]
    app_id = release["app_id"]
    platform = release["platform"]
    cert = publisher_gate.normalize_fingerprint(publisher["certificate_sha256"])
    if cert in history["revoked_signers"]:
        raise HistoryError("candidate signing identity has been revoked")
    parsed = semver_key(release["version"])
    entries = [entry for entry in history["releases"]
               if entry["app_id"] == app_id and entry["platform"] == platform]
    if entries:
        for entry in entries:
            if (entry["certificate_sha256"] != cert
                    or entry["source_repo"] != candidate["source_repo"]
                    or entry["package_id"] != candidate["package_id"]):
                raise HistoryError("publisher identity changed; explicit migration review required")
            if entry["artifact_sha256"] == release["sha256"]:
                raise HistoryError("previous release artifact replay")
        if parsed <= max(semver_key(entry["version"]) for entry in entries):
            raise HistoryError("version rollback or replay")
        if platform == "android" and candidate["version_code"] <= max(entry["version_code"] for entry in entries):
            raise HistoryError("Android versionCode rollback or replay")
    return {
        "app_id": app_id, "platform": platform, "version": release["version"],
        "version_code": candidate["version_code"], "source_repo": candidate["source_repo"],
        "package_id": candidate["package_id"], "certificate_sha256": cert,
        "artifact_sha256": release["sha256"], "status": "pending"
    }


def load_history(path):
    return validate_history(json.loads(Path(path).read_text(encoding="utf-8")))


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Check owner-reviewed continuity, never publish")
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--registry", type=Path, default=Path(__file__).resolve().parents[1] / "catalog/trusted_signers.json")
    parser.add_argument("--history", type=Path, default=Path(__file__).resolve().parents[1] / "catalog/release_history.json")
    args = parser.parse_args()
    try:
        candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
        registry = json.loads(args.registry.read_text(encoding="utf-8"))
        proposed = check_continuity(candidate, registry, load_history(args.history))
    except (OSError, ValueError, UnicodeError) as e:
        parser.exit(1, "REJECTED: " + str(e) + "\n")
    print(json.dumps({
        "candidate": proposed,
        "binary_signature_verified": False,
        "source_commit_verified": False,
        "public_release_authorized": False,
        "owner_review_required": True
    }, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
