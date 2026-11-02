#!/usr/bin/env python3
"""Offline candidate release hash/size gate. This does not verify signatures."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit, unquote

OWNER = "rezamahrm100-ops"
MAX_BYTES = 2 * 1024**3
ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
VERSION = re.compile(r"[0-9]+(?:\.[0-9]+){2}(?:-[0-9A-Za-z.-]+)?\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
PLATFORMS = {"android": {".apk"}, "windows": {".exe", ".msi", ".msix", ".msixbundle"}}


class IntegrityError(ValueError):
    pass


def validate_manifest(m):
    expected = {"app_id", "platform", "version", "asset_url", "sha256", "size_bytes"}
    if not isinstance(m, dict) or set(m) != expected:
        raise IntegrityError("invalid manifest schema")
    if not isinstance(m["app_id"], str) or not ID.fullmatch(m["app_id"]):
        raise IntegrityError("invalid app_id")
    if not isinstance(m["version"], str) or not VERSION.fullmatch(m["version"]):
        raise IntegrityError("invalid version")
    if m["platform"] not in PLATFORMS:
        raise IntegrityError("invalid platform")
    if not isinstance(m["sha256"], str) or not SHA256.fullmatch(m["sha256"]):
        raise IntegrityError("invalid sha256")
    if type(m["size_bytes"]) is not int or not 1 <= m["size_bytes"] <= MAX_BYTES:
        raise IntegrityError("invalid size_bytes")
    url = m["asset_url"]
    if not isinstance(url, str) or len(url) > 2048 or any(c in url for c in "\r\n\\"):
        raise IntegrityError("invalid asset_url")
    try:
        parsed = urlsplit(url)
        valid = (parsed.scheme == "https" and parsed.hostname == "github.com"
                 and not parsed.username and not parsed.password and parsed.port is None
                 and not parsed.query and not parsed.fragment)
    except ValueError as e:
        raise IntegrityError("malformed asset_url") from e
    if not valid:
        raise IntegrityError("untrusted asset_url")
    parts = parsed.path.strip("/").split("/")
    if (len(parts) != 6 or parts[0] != OWNER or not ID.fullmatch(parts[1])
            or parts[2:4] != ["releases", "download"]):
        raise IntegrityError("untrusted release path")
    if parts[4] not in {m["version"], "v" + m["version"]}:
        raise IntegrityError("release tag differs from version")
    if any(unquote(p) in (".", "..") or "%2f" in p.lower() or "%5c" in p.lower() for p in parts):
        raise IntegrityError("ambiguous or encoded path")
    if Path(parts[-1]).suffix.lower() not in PLATFORMS[m["platform"]]:
        raise IntegrityError("wrong artifact extension")
    return m


def verify_file(manifest, artifact):
    validate_manifest(manifest)
    path = Path(artifact)
    if path.is_symlink() or not path.is_file():
        raise IntegrityError("expected a regular file without symlinks")
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            size += len(block)
            if size > MAX_BYTES:
                raise IntegrityError("oversized asset")
            digest.update(block)
    if size != manifest["size_bytes"]:
        raise IntegrityError("size mismatch")
    if digest.hexdigest() != manifest["sha256"]:
        raise IntegrityError("sha256 mismatch")
    return {"app_id": manifest["app_id"], "version": manifest["version"],
            "platform": manifest["platform"], "asset_url": manifest["asset_url"],
            "sha256": digest.hexdigest(), "size_bytes": size,
            "integrity": "hash-and-size-verified", "signature_verified": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        receipt = verify_file(json.loads(args.manifest.read_text(encoding="utf-8")), args.artifact)
    except (IntegrityError, ValueError, OSError, UnicodeError) as exc:
        parser.exit(1, f"REJECTED: {exc}\n")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("HASH_OK SIGNATURE_NOT_CHECKED", receipt["sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
