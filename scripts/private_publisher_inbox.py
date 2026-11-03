#!/usr/bin/env python3
"""Owner-local, POSIX-only quarantined publisher submission inbox.

This is NOT a hosted upload service or identity/authentication provider.
All publisher identifiers are UNVERIFIED CLAIMS until separate owner review.
Never changes GitHub trust metadata, executes submitted packages, or publishes.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import stat
import sys
from urllib.parse import urlsplit

import binary_archive_review
import publisher_gate
import release_integrity

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ID = re.compile(r"[0-9a-f]{32}\Z")
EVENTS = {"request_review", "hold", "reject"}
MAX_METADATA = 32768
MAX_EVENTS = 100

class QuarantineError(ValueError):
    pass

def _private_dir(path):
    if os.name != "posix":
        raise QuarantineError("private quarantine requires POSIX owner/mode enforcement")
    raw = Path(path)
    if raw.is_symlink() or not raw.is_dir():
        raise QuarantineError("private quarantine directory missing or symlink")
    resolved = raw.resolve(strict=True)
    if resolved == PROJECT_ROOT or PROJECT_ROOT in resolved.parents:
        raise QuarantineError("private submissions cannot be inside public source checkout")
    info = resolved.stat()
    if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid()
            or info.st_mode & 0o077):
        raise QuarantineError("private quarantine must be owned by operator and mode 0700")
    return resolved

def init_root(path):
    if os.name != "posix":
        raise QuarantineError("POSIX security semantics are mandatory")
    dest = Path(path)
    resolved = dest.resolve()
    if dest.exists() or dest.is_symlink() or resolved == PROJECT_ROOT or PROJECT_ROOT in resolved.parents:
        raise QuarantineError("new private root required outside source checkout")
    dest.mkdir(mode=0o700, parents=False, exist_ok=False)
    dest.chmod(0o700)
    return _private_dir(dest)

def validate_claim(candidate, claimed_publisher):
    if not isinstance(candidate, dict) or set(candidate) != {
            "release", "source_repo", "source_sha", "package_id", "version_code"}:
        raise QuarantineError("untrusted candidate schema rejected")
    release = release_integrity.validate_manifest(candidate["release"])
    source = candidate["source_repo"]
    if (not isinstance(source, str) or not release_integrity.ID.fullmatch(source)
            or not isinstance(claimed_publisher, str) or not release_integrity.ID.fullmatch(claimed_publisher)
            or source != claimed_publisher
            or not isinstance(candidate["source_sha"], str)
            or not publisher_gate.COMMIT.fullmatch(candidate["source_sha"])):
        raise QuarantineError("invalid or inconsistent claimed source/publisher identity")
    parts = urlsplit(release["asset_url"]).path.strip("/").split("/")
    if parts[:2] != [publisher_gate.OWNER, source]:
        raise QuarantineError("claimed source disagrees with release repository")
    if release["platform"] == "android":
        if (not isinstance(candidate["package_id"], str)
                or not publisher_gate.PACKAGE.fullmatch(candidate["package_id"])
                or type(candidate["version_code"]) is not int
                or not 1 <= candidate["version_code"] <= 2**31 - 1):
            raise QuarantineError("Android package identity invalid")
    elif candidate["package_id"] is not None or candidate["version_code"] is not None:
        raise QuarantineError("Windows package/versionCode identity must be null")
    if len(json.dumps(candidate, ensure_ascii=False).encode("utf-8")) > MAX_METADATA:
        raise QuarantineError("candidate metadata too large")
    return release

def _write_private(path, data):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())

def _canonical(obj):
    return (json.dumps(obj, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":")) + "\n").encode("utf-8")

def _hash(data):
    return hashlib.sha256(data).hexdigest()

def _event(path, number, kind, previous_digest):
    payload = {
        "schema_version": 1, "sequence": number, "event": kind,
        "previous_event_sha256": previous_digest,
        "publisher_authenticated": False, "owner_review_approved": False,
        "public_distribution_authorized": False
    }
    target = path / "events" / f"{number:06d}.json"
    encoded = _canonical(payload)
    _write_private(target, encoded)
    return _hash(encoded)

def stage(root, candidate, artifact, claimed_publisher, *, make_id=secrets.token_hex):
    root = _private_dir(root)
    release = validate_claim(candidate, claimed_publisher)
    source = Path(artifact)
    if source.is_symlink() or not source.is_file():
        raise QuarantineError("expected real non-symlink candidate file")
    src = source.resolve(strict=True)
    if root == src or root in src.parents:
        raise QuarantineError("candidate input must be outside private quarantine")
    info = src.stat()
    ext = src.suffix.lower()
    if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
            or ext not in release_integrity.PLATFORMS[release["platform"]]
            or ext != Path(urlsplit(release["asset_url"]).path).suffix.lower()
            or not 0 < info.st_size <= release_integrity.MAX_BYTES):
        raise QuarantineError("file type, size or hardlink identity rejected")
    uid = make_id(16)
    if not isinstance(uid, str) or not ID.fullmatch(uid):
        raise QuarantineError("invalid random submission identifier")
    folder = root / uid
    if folder.exists() or folder.is_symlink():
        raise QuarantineError("refusing duplicate private intake identifier")
    folder.mkdir(mode=0o700)
    try:
        (folder / "events").mkdir(mode=0o700)
        target = folder / ("candidate" + ext)
        # Bound streaming, no shell or archive extraction; owner-controlled storage.
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(target, flags, 0o600)
        with os.fdopen(fd, "wb") as dst, src.open("rb") as stream:
            total = 0
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                total += len(chunk)
                if total > release_integrity.MAX_BYTES:
                    raise QuarantineError("oversized candidate while staging")
                dst.write(chunk)
            dst.flush()
            os.fsync(dst.fileno())
        # Hash source again to detect concurrent modification during copy.
        expected = release_integrity.verify_file(release, target)
        actual = release_integrity.verify_file(release, src)
        if expected["sha256"] != actual["sha256"]:
            raise QuarantineError("candidate changed during staging")
        archive = (binary_archive_review.review(target)
                   if ext in binary_archive_review.SUPPORTED else None)
        receipt = {
            "schema_version": 1,
            "submission_id": uid,
            "claimed_publisher": claimed_publisher,
            "claimed_source_sha": candidate["source_sha"],
            "app_id": release["app_id"],
            "platform": release["platform"],
            "version": release["version"],
            "artifact_sha256": expected["sha256"],
            "artifact_size_bytes": expected["size_bytes"],
            "archive_structure_checked": archive is not None,
            "publisher_identity_authenticated": False,
            "developer_certificate_verified": False,
            "source_attestation_verified": False,
            "antivirus_review_verified": False,
            "owner_release_approved": False,
            "production_distribution_authorized": False,
            "status": "quarantined"
        }
        _write_private(folder / "candidate.json", _canonical(candidate))
        _write_private(folder / "submission.json", _canonical(receipt))
        _event(folder, 1, "quarantined", None)
        return receipt
    except Exception:
        shutil.rmtree(folder)
        raise

def load(root, submission_id):
    root = _private_dir(root)
    if not isinstance(submission_id, str) or not ID.fullmatch(submission_id):
        raise QuarantineError("invalid submission reference")
    folder = _private_dir(root / submission_id)
    if folder.parent != root:
        raise QuarantineError("invalid publisher tenant directory")
    evidence = folder / "submission.json"
    if evidence.is_symlink() or not evidence.is_file():
        raise QuarantineError("missing private submission evidence")
    receipt = json.loads(evidence.read_text(encoding="utf-8"))
    if receipt.get("submission_id") != submission_id or receipt.get("production_distribution_authorized") is not False:
        raise QuarantineError("inconsistent submission metadata")
    return folder, receipt

def verify_events(folder):
    folder = _private_dir(folder)
    events_dir = _private_dir(folder / "events")
    entries = sorted(events_dir.iterdir())
    if not 1 <= len(entries) <= MAX_EVENTS:
        raise QuarantineError("event chain absent or unexpectedly long")
    previous = None
    status = "quarantined"
    for index, path in enumerate(entries, start=1):
        if path.is_symlink() or not path.is_file() or path.name != f"{index:06d}.json":
            raise QuarantineError("non-contiguous private event ledger")
        raw = path.read_bytes()
        if len(raw) > 4096:
            raise QuarantineError("oversized event")
        item = json.loads(raw)
        if (not isinstance(item, dict) or item.get("schema_version") != 1
                or item.get("sequence") != index
                or item.get("previous_event_sha256") != previous
                or item.get("publisher_authenticated") is not False
                or item.get("owner_review_approved") is not False
                or item.get("public_distribution_authorized") is not False
                or set(item) != {"schema_version", "sequence", "event",
                                  "previous_event_sha256", "publisher_authenticated",
                                  "owner_review_approved", "public_distribution_authorized"}):
            raise QuarantineError("private event chain integrity failure")
        event = item["event"]
        if index == 1 and event != "quarantined":
            raise QuarantineError("missing initial quarantine marker")
        if index > 1:
            if event not in EVENTS or status == "rejected":
                raise QuarantineError("invalid post-rejection or approval transition")
            status = "rejected" if event == "reject" else "held" if event == "hold" else "review_requested"
        previous = _hash(raw)
    return status, previous, len(entries)

def transition(root, submission_id, event):
    if event not in EVENTS:
        raise QuarantineError("no private intake command can approve/publish")
    folder, receipt = load(root, submission_id)
    current, previous, count = verify_events(folder)
    if current == "rejected":
        raise QuarantineError("rejected submissions cannot be reopened")
    if count >= MAX_EVENTS:
        raise QuarantineError("private event ledger full")
    _event(folder, count + 1, event, previous)
    return {
        "submission_id": receipt["submission_id"],
        "status": "rejected" if event == "reject" else "held" if event == "hold" else "review_requested",
        "owner_release_approved": False,
        "public_distribution_authorized": False
    }

def main():
    p = argparse.ArgumentParser(description="Owner-local private intake; never publish/approve")
    sub = p.add_subparsers(dest="action", required=True)
    init = sub.add_parser("init")
    init.add_argument("--root", type=Path, required=True)
    stage_p = sub.add_parser("stage")
    stage_p.add_argument("--root", type=Path, required=True)
    stage_p.add_argument("--candidate", type=Path, required=True)
    stage_p.add_argument("--artifact", type=Path, required=True)
    stage_p.add_argument("--claimed-publisher", required=True)
    review = sub.add_parser("mark")
    review.add_argument("--root", type=Path, required=True)
    review.add_argument("--id", required=True)
    review.add_argument("--event", choices=sorted(EVENTS), required=True)
    args = p.parse_args()
    try:
        if args.action == "init":
            root = init_root(args.root)
            print("PRIVATE_LOCAL_INBOX_INITIALIZED; EXTERNAL_AUTHENTICATION_NOT_CONFIGURED")
        elif args.action == "stage":
            candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
            output = stage(args.root, candidate, args.artifact, args.claimed_publisher)
            print(json.dumps(output, sort_keys=True))
        else:
            print(json.dumps(transition(args.root, args.id, args.event), sort_keys=True))
    except (OSError, ValueError, TypeError, KeyError, UnicodeError) as exc:
        p.exit(1, "PRIVATE_INTAKE_REJECTED: " + str(exc) + "\n")

if __name__ == "__main__":
    main()
