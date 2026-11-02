#!/usr/bin/env python3
"""Prepare and verify a same-bytes F-Droid signer keystore backup OFF the source disk.

Run exclusively in an owner-controlled offline POSIX signing workspace with an
already-approved keystore. No key generation, network, printing secret digests,
GitHub upload, source-repo writes or fake production readiness claims.
"""
import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path
import stat

SOURCE_ROOT = Path(__file__).resolve().parents[1]


class CustodyError(ValueError):
    pass


def private_regular(path, *, must_exist=True):
    path = Path(path)
    if path.is_symlink() or (must_exist and not path.is_file()):
        raise CustodyError("keystore must be an existing non-symlink regular file")
    resolved = path.resolve(strict=must_exist)
    if resolved == SOURCE_ROOT or SOURCE_ROOT in resolved.parents:
        raise CustodyError("signing keys/backups cannot be inside the public source checkout")
    if must_exist:
        mode = resolved.stat().st_mode
        if not stat.S_ISREG(mode) or (mode & 0o077):
            raise CustodyError("signer key must be a private regular file (0600 or stricter)")
        if resolved.stat().st_size < 256:
            raise CustodyError("keystore is unexpectedly small")
    return resolved


def private_backup_dir(path):
    directory = Path(path)
    if directory.is_symlink() or not directory.is_dir():
        raise CustodyError("an existing private backup directory is required")
    directory = directory.resolve(strict=True)
    if directory == SOURCE_ROOT or SOURCE_ROOT in directory.parents:
        raise CustodyError("backup destination cannot be in public checkout")
    if directory.stat().st_mode & 0o077:
        raise CustodyError("offline backup directory must be mode 0700 or stricter")
    return directory


def independent_volume(source, backup_dir):
    """Do not accept a second copy on the same device as an independent backup."""
    return source.stat().st_dev != backup_dir.stat().st_dev


def sha256_file(path):
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
            size += len(block)
    return digest.digest(), size


def validate_backup(source, backup, volume_check=independent_volume):
    if os.name != "posix":
        raise CustodyError("offline signer custody currently requires POSIX file permissions")
    source = private_regular(source)
    backup = private_regular(backup)
    if source == backup or not volume_check(source, backup.parent):
        raise CustodyError("keystore copy must be on an independent storage volume")
    src_hash, src_size = sha256_file(source)
    dst_hash, dst_size = sha256_file(backup)
    if src_size != dst_size or not hmac.compare_digest(src_hash, dst_hash):
        raise CustodyError("independent offline keystore backup differs from source")
    return {"schema_version": 1,
            "byte_for_byte_backup_verified": True,
            "separate_storage_volume_checked": True,
            "public_upload_performed": False,
            "offline_disconnection_physically_verified": False,
            "restore_and_sign_drill_verified": False,
            "production_publishing_authorized": False}


def create_backup(source, backup_dir, filename, volume_check=independent_volume):
    if os.name != "posix":
        raise CustodyError("offline signer custody currently requires POSIX file permissions")
    src = private_regular(source)
    directory = private_backup_dir(backup_dir)
    if not volume_check(src, directory):
        raise CustodyError("backup must use independent storage volume, not same-disk folder")
    if (not isinstance(filename, str) or not filename or
            filename in {".", ".."} or "/" in filename or "\\" in filename or filename.startswith(".")):
        raise CustodyError("invalid backup filename")
    output = directory / filename
    if output.exists() or output.is_symlink():
        raise CustodyError("refusing to overwrite an existing backup")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    fd = None
    created = False
    try:
        fd = os.open(output, flags, 0o600)
        created = True
        with os.fdopen(fd, "wb") as dst, src.open("rb") as stream:
            fd = None
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                dst.write(chunk)
            dst.flush()
            os.fsync(dst.fileno())
        # Independent verification of copied bytes, file mode and filesystem.
        receipt = validate_backup(src, output, volume_check=volume_check)
        return receipt
    except Exception:
        if created:
            output.unlink(missing_ok=True)
        raise
    finally:
        if fd is not None:
            os.close(fd)


def main():
    parser = argparse.ArgumentParser(description="Owner-only OFFLINE keystore backup, no network")
    parser.add_argument("--keystore", required=True, type=Path)
    parser.add_argument("--offline-backup-dir", required=True, type=Path)
    parser.add_argument("--backup-name", required=True)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()
    try:
        # Receipt also must remain outside the public checkout and never overwrite.
        if args.receipt.exists() or args.receipt.is_symlink():
            raise CustodyError("refusing to overwrite an existing receipt")
        receipt_parent = private_backup_dir(args.receipt.parent)
        if args.receipt.resolve() == args.keystore.resolve():
            raise CustodyError("receipt cannot replace a keystore")
        result = create_backup(args.keystore, args.offline_backup_dir, args.backup_name)
        with (receipt_parent / args.receipt.name).open("x", encoding="utf-8") as fd:
            json.dump(result, fd, indent=2, sort_keys=True)
            fd.write("\n")
        os.chmod(args.receipt, 0o600)
    except (OSError, ValueError) as exc:
        parser.exit(1, "OFFLINE_BACKUP_REJECTED: " + str(exc) + "\n")
    print("INDEPENDENT_VOLUME_BACKUP_MATCHED; PHYSICAL_OFFLINE_AND_RESTORE_NOT_VERIFIED")


if __name__ == "__main__":
    main()
