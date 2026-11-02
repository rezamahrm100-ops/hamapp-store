#!/usr/bin/env python3
"""Fail-closed F-Droid signed-index v2 preflight using upstream fdroidserver.

Owner must independently pin both the HTTPS origin and repository signing-key
SHA-256 fingerprint. No key generation, catalogue publication or package install.
"""
import argparse
import ipaddress
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_android_catalog

HOST = re.compile(r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")


class SignedIndexError(ValueError):
    pass


def validate_public_repo(config, expected_url, expected_fingerprint):
    try:
        repo = build_android_catalog.validate_repository(config)
    except (ValueError, TypeError) as exc:
        raise SignedIndexError("repository configuration rejected") from exc
    if repo is None:
        raise SignedIndexError("no production F-Droid signing repository is approved")
    if not isinstance(expected_url, str) or repo["url"] != expected_url:
        raise SignedIndexError("repo origin does not match independently pinned URL")
    if not isinstance(expected_fingerprint, str) or repo["fingerprint"] != expected_fingerprint.upper():
        raise SignedIndexError("signing key does not match independently pinned certificate fingerprint")
    url = urlsplit(repo["url"])
    host = url.hostname
    if host is None or not HOST.fullmatch(host) or host.endswith((".local", ".localhost", ".internal", ".test", ".example")):
        raise SignedIndexError("host must be an approved public DNS origin")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        pass
    else:
        raise SignedIndexError("direct IP origins are not eligible")
    return repo


def verify_signed_index(config, expected_url, expected_fingerprint, downloader=None):
    """downloader is injectable ONLY for unit tests; real CLI loads fdroidserver."""
    repo = validate_public_repo(config, expected_url, expected_fingerprint)
    if downloader is None:
        try:
            from fdroidserver.index import download_repo_index_v2
        except ImportError as exc:
            raise SignedIndexError("trusted workspace requires official fdroidserver") from exc
        downloader = download_repo_index_v2
    # verify_fingerprint=True must never be overridden. F-Droid verifies the
    # signed v2 entry and its index digest with the pinned signing fingerprint.
    uri = repo["url"] + "?fingerprint=" + repo["fingerprint"]
    try:
        result = downloader(uri, verify_fingerprint=True, timeout=60)
    except Exception as exc:
        raise SignedIndexError("upstream F-Droid signature/index verification failed") from exc
    if not isinstance(result, tuple) or len(result) != 2:
        raise SignedIndexError("invalid fdroidserver verification response")
    index, _etag = result
    if not isinstance(index, dict) or not isinstance(index.get("repo"), dict) or not isinstance(index.get("packages"), dict):
        raise SignedIndexError("missing mandatory signed index-v2 structures")
    return {
        "schema_version": 1,
        "repository_url": repo["url"],
        "pinned_signer_sha256": repo["fingerprint"],
        "index_v2_signature_verifier": "fdroidserver.index.download_repo_index_v2",
        "index_v2_verified_with_pinned_key": True,
        "package_count": len(index["packages"]),
        "owner_publishing_approved": False,
        "private_signing_key_managed": False,
        "live_apk_install_update_verified": False,
        "production_store_ready": False,
    }


def main():
    parser = argparse.ArgumentParser(description="Verify a trusted signed F-Droid v2 index")
    parser.add_argument("--config", type=Path, default=ROOT / "catalog/android_repository.json")
    parser.add_argument("--expected-url", required=True)
    parser.add_argument("--expected-fingerprint", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.receipt.exists() or args.receipt.is_symlink():
            raise SignedIndexError("refusing to overwrite existing audit receipt")
        config = json.loads(args.config.read_text(encoding="utf-8"))
        receipt = verify_signed_index(config, args.expected_url, args.expected_fingerprint)
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, ValueError, UnicodeError) as exc:
        parser.exit(1, "FDROID_INDEX_REJECTED: " + str(exc) + "\n")
    print("FDROID_SIGNED_INDEX_V2_VERIFIED; PACKAGE_INSTALL_NOT_APPROVED")


if __name__ == "__main__":
    raise SystemExit(main())
