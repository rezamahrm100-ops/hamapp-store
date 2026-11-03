#!/usr/bin/env python3
"""Prove official F-Droid stored a genuine repository in its SQLite DB.

Only introspects a fresh, disposable, rooted Android emulator running the
actual independently verified F-Droid APK. The private DB snapshot is deleted
before any upload, never reads an owner device or writes a repo DB record.
HTTP fetch alone is NOT evidence of repository registration.
"""
import argparse
from contextlib import closing
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import tarfile
import tempfile

HOST = "10.0.2.2:8975"
EXPECTED_SHA40 = re.compile(r"[a-f0-9]{40}\Z")
EXPECTED_FP64 = re.compile(r"[A-Fa-f0-9]{64}\Z")
# F-Droid's initial official catalogue can create >48MiB of genuine SQLite
# and WAL bytes on a fresh emulator. Keep bounded private temporary memory,
# never upload the snapshot, but accommodate the real upstream app's DB size.
MAX_SNAPSHOT = 384 * 1024 * 1024
MAX_DB = 256 * 1024 * 1024


class RepositoryPersistenceError(ValueError):
    pass


def inspect_sqlite(path, expected_host=HOST):
    if not path.is_file() or path.is_symlink() or not 0 < path.stat().st_size <= MAX_DB:
        raise RepositoryPersistenceError("regular bounded SQLite file required")
    uri = path.resolve(strict=True).as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True, timeout=3)) as conn:
        conn.execute("PRAGMA query_only=ON")
        check = conn.execute("PRAGMA quick_check(1)").fetchone()
        if not check or check[0] != "ok":
            raise RepositoryPersistenceError("F-Droid SQLite integrity check failed")
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
        if len(tables) > 150:
            raise RepositoryPersistenceError("unexpected huge official client table count")
        matched = []
        for (table_name,) in tables:
            if (not isinstance(table_name, str) or len(table_name) > 128
                    or not re.fullmatch(r"[A-Za-z0-9_]+", table_name)):
                continue
            if "repo" not in table_name.lower():
                continue
            cursor = conn.execute('SELECT * FROM "' + table_name + '" LIMIT 5001')
            rows = cursor.fetchall()
            if len(rows) > 5000:
                raise RepositoryPersistenceError("unbounded F-Droid repository DB table")
            for row in rows:
                strings = [value if isinstance(value, str)
                           else value.decode("utf-8", errors="ignore")
                           for value in row if isinstance(value, (bytes, str))]
                if any(expected_host in value for value in strings):
                    matched.append(table_name)
        return matched


def validate_tar_snapshot(raw, target):
    if not 0 < len(raw) <= MAX_SNAPSHOT:
        raise RepositoryPersistenceError("official client DB archive absent or oversized, bytes=" + str(len(raw)))
    allowed_names = re.compile(r"databases/[A-Za-z0-9._-]{1,130}\Z")
    files = []
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:*") as archive:
        for member in archive:
            if member.isdir():
                continue
            if (not member.isfile() or member.issym() or member.islnk()
                    or member.size > MAX_DB or not allowed_names.fullmatch(member.name)):
                raise RepositoryPersistenceError("unsafe private F-Droid database archive entry")
            basename = member.name.split("/", 1)[1]
            if (basename.startswith(".") or ".." in basename or len(files) >= 60):
                raise RepositoryPersistenceError("unsafe or excessive private DB entries")
            content = archive.extractfile(member).read(member.size + 1)
            if len(content) != member.size:
                raise RepositoryPersistenceError("truncated private DB entry")
            filename = member.name.split("/", 1)[1]
            output = target / filename
            if output.exists():
                raise RepositoryPersistenceError("duplicate DB archive file")
            with output.open("xb") as stream:
                stream.write(content)
            output.chmod(0o600)
            files.append(output)
    return [path for path in files
            if path.name.endswith((".db", ".sqlite", ".sqlite3"))
            or (not path.name.endswith(("-wal", "-shm", "-journal"))
                and path.read_bytes()[:16] == b"SQLite format 3\x00")]


def verify(source_sha, fingerprint, receipt_path):
    if (os.name != "posix" or os.environ.get("GITHUB_ACTIONS") != "true"
            or os.environ.get("RUNNER_OS") != "Linux"):
        raise RepositoryPersistenceError("disposable GitHub-hosted Android lab only")
    if not EXPECTED_SHA40.fullmatch(source_sha) or not EXPECTED_FP64.fullmatch(fingerprint):
        raise RepositoryPersistenceError("immutable test source SHA and repository signer pin required")
    if receipt_path.exists() or receipt_path.is_symlink():
        raise RepositoryPersistenceError("must not overwrite proof receipt")
    uid = subprocess.run(["adb", "shell", "id", "-u"],
                         capture_output=True, text=True, timeout=15, check=False)
    if uid.returncode != 0 or uid.stdout.strip() != "0":
        raise RepositoryPersistenceError("fresh disposable emulator is not rooted")
    # This command merely snapshots private DB files from a disposable CI
    # emulator; it never mutates the app's actual DB.
    archive = subprocess.run([
        "adb", "exec-out", "tar", "-C",
        "/data/user/0/org.fdroid.fdroid", "-cf", "-", "databases",
    ], capture_output=True, timeout=40, check=False)
    if archive.returncode:
        raise RepositoryPersistenceError("official upstream app has no readable DB snapshot")
    runner = Path(os.environ["RUNNER_TEMP"]).resolve(strict=True)
    with tempfile.TemporaryDirectory(prefix="hamapp-private-fdroid-db-", dir=runner) as private:
        snapshots = validate_tar_snapshot(archive.stdout, Path(private))
        if not snapshots:
            raise RepositoryPersistenceError("official F-Droid has no SQLite database to inspect")
        validated = []
        for file in snapshots:
            try:
                matches = inspect_sqlite(file)
            except (sqlite3.DatabaseError, RepositoryPersistenceError):
                continue
            if matches:
                validated.append((file, matches))
        if len(validated) != 1:
            raise RepositoryPersistenceError(
                "exactly one intact official-client SQLite repository record required")
        db_file, tables = validated[0]
        result = {
            "schema_version": 1,
            "scope": "isolated-official-fdroid-client-native-SQLite-persistence",
            "source_sha": source_sha,
            "independently_verified_ephemeral_repository_fingerprint": fingerprint.upper(),
            "real_official_client_repo_host_saved_in_native_sqlite": True,
            "actual_client_database_read_only_integrity_check_passed": True,
            "matched_repo_table_count": len(tables),
            "private_emulator_sqlite_sha256_for_evidence_only": hashlib.sha256(
                db_file.read_bytes()).hexdigest(),
            "signature_fingerprint_persisted_in_client_database_verified": False,
            "client_installed_apk_from_repo_verified": False,
            "client_updated_apk_from_repo_verified": False,
            "owner_device_or_production_repo_approved": False,
        }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    with receipt_path.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print("ACTUAL_OFFICIAL_FDROID_NATIVE_REPO_SQLITE_PERSISTENCE_VERIFIED_NOT_APP_INSTALL")
    return result


def main():
    parser = argparse.ArgumentParser(description="Read-only official F-Droid repo SQLite proof")
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--fingerprint", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    try:
        verify(args.source_sha, args.fingerprint, args.receipt)
    except (OSError, ValueError, sqlite3.DatabaseError,
            subprocess.TimeoutExpired, tarfile.TarError) as exc:
        parser.exit(1, "ACTUAL_OFFICIAL_FDROID_REPO_DB_PROOF_FAILED: " + str(exc) + "\n")


if __name__ == "__main__":
    main()
