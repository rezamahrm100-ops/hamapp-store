#!/usr/bin/env python3
"""Offline structural archive inspection of ACTUAL APK/MSIX artifact bytes.

Checks archive entry paths, duplicates, encryption, POSIX symlinks, CRC,
decompression bounds and file identity across the scan. Does NOT establish
malware absence, safe executable code, publisher identity or permission to
publish. No network, third-party dependencies, signing keys or file extraction.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import stat
import unicodedata
import zipfile

SUPPORTED = {".apk", ".msix", ".msixbundle"}
MAX_ARCHIVE = 2 * 1024**3
MAX_ENTRIES = 100000
MAX_TOTAL_UNCOMPRESSED = 4 * 1024**3
MAX_ENTRY_UNCOMPRESSED = 2 * 1024**3
MAX_RATIO = 3000
CHUNK = 1024 * 1024

class ArchiveReviewError(ValueError):
    pass

def file_hash(path):
    h = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK), b""):
            size += len(chunk)
            if size > MAX_ARCHIVE:
                raise ArchiveReviewError("archive exceeds size limit")
            h.update(chunk)
    if size == 0:
        raise ArchiveReviewError("empty archive")
    return h.hexdigest(), size

def checked_entry(info, seen):
    name = info.filename
    if (not isinstance(name, str) or not name or len(name) > 512
            or "\x00" in name or "\\" in name or name.startswith("/")
            or "//" in name or ":" in name
            or any(ord(char) < 32 for char in name)):
        raise ArchiveReviewError("unsafe archive entry path")
    normalized = unicodedata.normalize("NFC", name)
    segments = normalized.rstrip("/").split("/")
    if not segments or any(segment in ("", ".", "..") for segment in segments):
        raise ArchiveReviewError("archive traversal or ambiguous path")
    logical = normalized.rstrip("/").casefold()
    if logical in seen:
        raise ArchiveReviewError("duplicate or case-colliding archive entry")
    seen.add(logical)
    if info.flag_bits & 0x1:
        raise ArchiveReviewError("encrypted archive entry rejected")
    if info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
        raise ArchiveReviewError("unsupported compressed entry format")
    if info.create_system == 3 and stat.S_ISLNK(info.external_attr >> 16):
        raise ArchiveReviewError("symbolic-link archive entry rejected")
    if not 0 <= info.file_size <= MAX_ENTRY_UNCOMPRESSED:
        raise ArchiveReviewError("single entry expands beyond safe limit")
    if info.file_size and (info.compress_size == 0 or
                            info.file_size / info.compress_size > MAX_RATIO):
        raise ArchiveReviewError("archive compression ratio exceeds safe limit")
    return normalized

def review(artifact):
    path = Path(artifact)
    if (path.is_symlink() or not path.is_file()
            or path.suffix.lower() not in SUPPORTED):
        raise ArchiveReviewError("expected non-symlink APK/MSIX file")
    before_hash, before_size = file_hash(path)
    try:
        with zipfile.ZipFile(path, "r", allowZip64=True) as archive:
            entries = archive.infolist()
            if not 1 <= len(entries) <= MAX_ENTRIES:
                raise ArchiveReviewError("invalid number of archive entries")
            seen = set()
            total_declared = 0
            for info in entries:
                checked_entry(info, seen)
                total_declared += info.file_size
                if total_declared > MAX_TOTAL_UNCOMPRESSED:
                    raise ArchiveReviewError("total decompressed archive size exceeds limit")
            actual_total = 0
            for info in entries:
                if info.is_dir():
                    if info.file_size != 0:
                        raise ArchiveReviewError("directory contains data")
                    continue
                amount = 0
                # ZipFile.open enforces CRC checks when the entire entry is read.
                with archive.open(info, "r") as stream:
                    for block in iter(lambda: stream.read(CHUNK), b""):
                        amount += len(block)
                        actual_total += len(block)
                        if (amount > info.file_size or
                                actual_total > MAX_TOTAL_UNCOMPRESSED):
                            raise ArchiveReviewError("archive decompression bound exceeded")
                if amount != info.file_size:
                    raise ArchiveReviewError("archive entry size mismatch")
    except (zipfile.BadZipFile, EOFError, OSError, RuntimeError,
            NotImplementedError, UnicodeError) as exc:
        raise ArchiveReviewError("actual archive parsing or CRC verification failed") from exc
    after_hash, after_size = file_hash(path)
    if (before_hash, before_size) != (after_hash, after_size):
        raise ArchiveReviewError("artifact mutated during inspection")
    return {
        "schema_version": 1,
        "artifact_sha256": before_hash,
        "size_bytes": before_size,
        "archive_entry_count": len(entries),
        "total_uncompressed_bytes": actual_total,
        "actual_archive_crc_and_paths_checked": True,
        "archive_symlinks_and_traversal_rejected": True,
        "malware_free_verified": False,
        "developer_signature_verified": False,
        "publisher_permission_approved": False,
        "public_release_authorized": False,
    }

def main():
    p = argparse.ArgumentParser(description="Inspect actual APK/MSIX archive bytes, NOT malware clearance")
    p.add_argument("--artifact", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    args = p.parse_args()
    try:
        if args.receipt.exists() or args.receipt.is_symlink():
            raise ArchiveReviewError("refusing to overwrite an existing receipt")
        result = review(args.artifact)
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        with args.receipt.open("x", encoding="utf-8") as output:
            json.dump(result, output, ensure_ascii=False, sort_keys=True, indent=2)
            output.write("\n")
    except (OSError, ValueError) as exc:
        p.exit(1, "ARCHIVE_REJECTED: " + str(exc) + "\n")
    print("ACTUAL_ARCHIVE_CRC_AND_STRUCTURE_VERIFIED; NOT_MALWARE_OR_PUBLIC_RELEASE_APPROVAL")

if __name__ == "__main__":
    main()
