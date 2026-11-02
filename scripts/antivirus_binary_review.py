#!/usr/bin/env python3
"""Perform a REAL ClamAV signature scan of the exact local APK/EXE/MSIX bytes.

Requires ClamAV with a recent database. Fail closed on outdated/missing DB,
scanner errors, timeouts, detections and file mutation. No untrusted commands,
shell or extractions. A negative signature scan CANNOT prove malware absence.
"""
import argparse
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import re
import subprocess

EXTENSIONS = {".apk", ".exe", ".msi", ".msix", ".msixbundle"}
MAX_BYTES = 2 * 1024**3
VERSION = re.compile(r"^ClamAV\s+([^/\s]+)/(\d+)/(.+)$")

class MalwareReviewError(ValueError):
    pass

def hash_file(path):
    h = hashlib.sha256()
    total = 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            total += len(block)
            if total > MAX_BYTES:
                raise MalwareReviewError("binary too large for standard review")
            h.update(block)
    if total == 0:
        raise MalwareReviewError("empty binary")
    return (h.hexdigest(), total)

def call(command, runner, timeout):
    try:
        result = runner(command, shell=False, capture_output=True,
                        text=True, timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise MalwareReviewError("ClamAV scanner unavailable or timed out") from exc
    if (not isinstance(result.returncode, int) or
            not isinstance(result.stdout, str) or
            not isinstance(result.stderr, str) or
            len(result.stdout) > 100000 or len(result.stderr) > 100000):
        raise MalwareReviewError("unexpected ClamAV scanner output")
    return result

def check_database_version(raw, *, now=None, max_age_days=14):
    if not isinstance(raw, str):
        raise MalwareReviewError("no reliable ClamAV signature database")
    m = VERSION.fullmatch(raw.strip())
    if m is None:
        raise MalwareReviewError("ClamAV engine/signature DB version is missing")
    engine, signature_version, rawdate = m.groups()
    try:
        db_date = datetime.strptime(rawdate.strip(), "%a %b %d %H:%M:%S %Y")
    except ValueError as exc:
        raise MalwareReviewError("unparseable ClamAV database timestamp") from exc
    db_date = db_date.replace(tzinfo=timezone.utc)
    current = now or datetime.now(timezone.utc)
    delta = current - db_date
    if delta > timedelta(days=max_age_days) or delta < -timedelta(days=1):
        raise MalwareReviewError("ClamAV signature database is stale or future-dated")
    return engine, int(signature_version), db_date.date().isoformat()

def scan(artifact, *, scanner="clamscan", runner=subprocess.run, now=None):
    path = Path(artifact)
    if path.is_symlink() or not path.is_file() or path.suffix.lower() not in EXTENSIONS:
        raise MalwareReviewError("expected genuine non-symlink APK/Windows installer file")
    before = hash_file(path)
    version = call([scanner, "--version"], runner, 45)
    if version.returncode != 0:
        raise MalwareReviewError("ClamAV has no usable signature database")
    engine, database, date = check_database_version(version.stdout, now=now)
    command = [
        scanner, "--infected", "--no-summary", "--stdout",
        "--alert-exceeds-max=yes", "--",
        str(path.resolve(strict=True))
    ]
    result = call(command, runner, 600)
    if result.returncode == 1:
        raise MalwareReviewError("ClamAV reported a malware signature or exceeded scan limits")
    if result.returncode != 0:
        raise MalwareReviewError("ClamAV did not complete a clean signature scan")
    after = hash_file(path)
    if after != before:
        raise MalwareReviewError("binary changed during antivirus review")
    return {
        "schema_version": 1,
        "artifact_sha256": before[0], "artifact_bytes": before[1],
        "engine": "ClamAV", "engine_version": engine,
        "database_version": database, "database_date_utc": date,
        "actual_signature_scan_completed_without_detection": True,
        "malware_absence_verified": False,
        "runtime_behaviour_sandbox_checked": False,
        "developer_signature_verified": False,
        "public_distribution_authorized": False,
    }

def main():
    p = argparse.ArgumentParser(description="Real local ClamAV signature scan, NOT malware-free approval")
    p.add_argument("--artifact", type=Path, required=True)
    p.add_argument("--scanner", default="clamscan")
    p.add_argument("--receipt", type=Path, required=True)
    args = p.parse_args()
    try:
        if args.receipt.exists() or args.receipt.is_symlink():
            raise MalwareReviewError("cannot overwrite an antivirus review receipt")
        receipt = scan(args.artifact, scanner=args.scanner)
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        with args.receipt.open("x", encoding="utf-8") as out:
            json.dump(receipt, out, indent=2, sort_keys=True)
            out.write("\n")
    except (OSError, ValueError) as exc:
        p.exit(1, "ANTIVIRUS_REVIEW_REJECTED: " + str(exc) + "\n")
    print("ACTUAL_CLAMAV_SIGNATURE_SCAN_CLEAN; MALWARE_ABSENCE_NOT_VERIFIED")

if __name__ == "__main__":
    main()
