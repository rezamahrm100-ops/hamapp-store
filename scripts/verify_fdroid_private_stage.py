#!/usr/bin/env python3
"""Offline cryptographic verification of ACTUAL private F-Droid signed index-v2.

Uses the upstream fdroidserver JAR signature verifier, checks owner-pinned
repo certificate, signed entry's index SHA-256/size and the intended APK's
exact package/versionCode/versionName/size/digest. Never serves local keys over
HTTP or uploads private config. No production publishing or device install.
"""
import hashlib
import json
import os
from pathlib import Path
import re

import publisher_gate
import release_integrity

HEX = re.compile(r"[0-9a-fA-F]{64}\Z")
MAX_INDEX = 50 * 1024 * 1024
MAX_JAR = 10 * 1024 * 1024

class PrivateIndexError(ValueError):
    pass

def checked_sha(value):
    if not isinstance(value, str) or not HEX.fullmatch(value):
        raise PrivateIndexError("expected independently pinned 64-hex repository fingerprint/digest")
    return value.upper()

def load_raw_file(path, maximum):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= maximum:
        raise PrivateIndexError("required local signed index file absent or oversized")
    return path.read_bytes()

def _match_package(index, package_id, version_code, version_name, binary_sha, binary_size):
    if not isinstance(index, dict) or not isinstance(index.get("packages"), dict):
        raise PrivateIndexError("signed index-v2 lacks packages")
    item = index["packages"].get(package_id)
    if not isinstance(item, dict) or not isinstance(item.get("versions"), dict):
        raise PrivateIndexError("intended package is not listed in signed index")
    matching_files = []
    for version in item["versions"].values():
        if not isinstance(version, dict):
            continue
        file = version.get("file")
        manifest = version.get("manifest")
        if not isinstance(file, dict) or not isinstance(manifest, dict):
            continue
        if (file.get("sha256") == binary_sha
                and type(file.get("size")) is int and file["size"] == binary_size
                and type(manifest.get("versionCode")) is int
                and manifest["versionCode"] == version_code
                and manifest.get("versionName") == version_name):
            matching_files.append(file.get("name"))
    if len(matching_files) != 1:
        raise PrivateIndexError("exact immutable APK version/digest not uniquely indexed")
    name = matching_files[0]
    if (not isinstance(name, str) or not re.fullmatch(r"/[A-Za-z0-9._+-]+\.apk", name)
            or ".." in name or "%" in name):
        raise PrivateIndexError("signed index listed unsafe APK filename")
    return name[1:]

def verify(workspace, expected_fingerprint, candidate, *, loader=None):
    expected_fp = checked_sha(expected_fingerprint)
    if not isinstance(candidate, dict) or candidate.get("release", {}).get("platform") != "android":
        raise PrivateIndexError("only owner-reviewed Android APK candidates may be indexed")
    manifest = release_integrity.validate_manifest(candidate["release"])
    if (not isinstance(candidate.get("package_id"), str)
            or not publisher_gate.PACKAGE.fullmatch(candidate["package_id"])
            or type(candidate.get("version_code")) is not int
            or not 1 <= candidate["version_code"] <= 2**31 - 1):
        raise PrivateIndexError("invalid Android package identity")
    repo = Path(workspace) / "repo"
    if repo.is_symlink() or not repo.is_dir():
        raise PrivateIndexError("expected private F-Droid repo directory")
    jar = repo / "entry.jar"
    indexfile = repo / "index-v2.json"
    load_raw_file(jar, MAX_JAR)
    rawindex = load_raw_file(indexfile, MAX_INDEX)

    if loader is None:
        try:
            from fdroidserver.index import get_index_from_jar
        except ImportError as exc:
            raise PrivateIndexError("official fdroidserver signing verifier not installed") from exc
        loader = get_index_from_jar
    try:
        # Upstream JAR certificate signature verifier; no JSON success flags
        # or unverified, user-supplied fingerprints in real CLI path.
        entry, _key, observed_fp = loader(str(jar), fingerprint=expected_fp)
    except Exception as exc:
        raise PrivateIndexError("real F-Droid entry JAR signature verification failed") from exc
    if checked_sha(observed_fp) != expected_fp:
        raise PrivateIndexError("F-Droid signing certificate is not owner-pinned key")
    if not isinstance(entry, dict) or not isinstance(entry.get("index"), dict):
        raise PrivateIndexError("signed JAR entry metadata malformed")
    link = entry["index"]
    if (link.get("name") not in ("/index-v2.json", "index-v2.json")
            or not isinstance(link.get("sha256"), str)
            or checked_sha(link["sha256"]) != hashlib.sha256(rawindex).hexdigest().upper()
            or type(link.get("size")) is not int or link["size"] != len(rawindex)):
        raise PrivateIndexError("index-v2 data is not the bytes committed by signed JAR")
    try:
        index = json.loads(rawindex.decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise PrivateIndexError("malformed signed index JSON") from exc
    listed_filename = _match_package(index, candidate["package_id"], candidate["version_code"],
                   manifest["version"], manifest["sha256"], manifest["size_bytes"])
    # Do not accept signed JSON metadata as a substitute for the ACTUAL local
    # downloadable APK. The exact locally staged file must be a regular
    # non-linked file under this repository and match the immutable candidate.
    listed_apk = repo / listed_filename
    if (listed_apk.is_symlink() or not listed_apk.is_file()
            or listed_apk.stat().st_nlink != 1):
        raise PrivateIndexError("signed index APK is absent, linked or unsafe")
    try:
        verified_file = release_integrity.verify_file(manifest, listed_apk)
    except (OSError, ValueError) as exc:
        raise PrivateIndexError("signed indexed APK bytes mismatch") from exc
    if verified_file["sha256"] != manifest["sha256"]:
        raise PrivateIndexError("signed indexed APK digest mismatch")
    return {
        "schema_version": 1,
        "local_index_signed_with_pinned_repository_key": True,
        "signed_entry_sha256": hashlib.sha256(jar.read_bytes()).hexdigest(),
        "index_v2_sha256": hashlib.sha256(rawindex).hexdigest(),
        "repo_signer_fingerprint": expected_fp,
        "indexed_package_id": candidate["package_id"],
        "indexed_version_code": candidate["version_code"],
        "indexed_apk_sha256": manifest["sha256"],
        "indexed_repo_apk_file_sha256_verified": True,
        "public_https_repository_verified": False,
        "official_fdroid_client_install_tested": False,
        "owner_publishing_approved": False,
        "production_store_ready": False,
    }
