#!/usr/bin/env python3
"""Reproducible no-secret HamApp backend service kit.

No production credentials, signatures, live accounts, signer keys, auth
tokens, local Docker state or proprietary packages are copied into the kit.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILE_LIST = (
    "README.md",
    ".dockerignore",
    "deployment/Dockerfile",
    "deployment/Dockerfile.owner-review",
    "deployment/owner-review-entrypoint.sh",
    "deployment/compose.yaml",
    "deployment/README_FA.md",
    "deployment/HamApp-Service-Setup.cmd",
    "deployment/HamApp-Service-Status.cmd",
    "deployment/HamApp-Service-Tokens.cmd",
    "deployment/HamApp-Service-Stop.cmd",
    "windows_client/__init__.py",
    "windows_client/publisher_connection.py",
    "docs/OWNER-NO-CODE-CONNECTIONS-2026-11-08.md",
    "docs/REMOTE-PUBLISHER-TLS-QUARANTINE.md",
    "docs/FDROID-KEY-CUSTODY.md",
    "catalog/trusted_signers.json",
    "catalog/release_history.json",
    "catalog/android_repository.json",
)
EXCLUDE = re.compile(r"(^|/)(?:\.env|credentials|id_rsa|private|secret|token)(?:\..*)?$", re.I)
FILE_MAX = 1024 * 1024
KIT_MAX = 20 * 1024 * 1024

class KitError(ValueError):
    pass

def files():
    chosen = set(FILE_LIST)
    chosen.update(p.relative_to(ROOT).as_posix()
                  for p in (ROOT / "scripts").glob("*.py") if p.is_file())
    chosen.update(p.relative_to(ROOT).as_posix()
                  for p in (ROOT / "scripts").glob("*.cmd") if p.is_file())
    if not chosen:
        raise KitError("no service files")
    result = {}
    total = 0
    for path in sorted(chosen):
        if path.startswith("/") or ".." in Path(path).parts or EXCLUDE.search(path):
            raise KitError("forbidden private path")
        obj = ROOT / path
        if obj.is_symlink() or not obj.is_file():
            raise KitError("packaging input missing or symlink")
        if obj.stat().st_size > FILE_MAX:
            raise KitError("excessive service source input")
        raw = obj.read_bytes()
        total += len(raw)
        if total > KIT_MAX:
            raise KitError("service kit exceeds reviewed size limit")
        result[path] = raw
    return result

def build(destination, *, source_sha=None):
    if source_sha is not None and not re.fullmatch(r"[a-f0-9]{40}", source_sha):
        raise KitError("invalid immutable source SHA")
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise KitError("do not overwrite previously built artifacts")
    payload = files()
    metadata = {
        "schema_version": 1,
        "kind": "hamapp-private-quarantine-service-kit",
        "source_sha": source_sha,
        "production_signed": False,
        "publisher_approved": False,
        "public_distribution_authorized": False,
        "deployment_proven": False,
        "files": {p: hashlib.sha256(raw).hexdigest()
                  for p, raw in payload.items()},
    }
    payload["service-kit-manifest.json"] = (
        json.dumps(metadata, sort_keys=True, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(destination, mode="x",
                             compression=zipfile.ZIP_DEFLATED,
                             compresslevel=9, allowZip64=False) as archive:
            for name, raw in sorted(payload.items()):
                info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (0o100644 << 16)
                archive.writestr(info, raw)
        return {"zip": str(destination), "sha256": hashlib.sha256(
                destination.read_bytes()).hexdigest(),
                "entries": len(payload),
                "production_signed": False,
                "source_sha": source_sha}
    except BaseException:
        destination.unlink(missing_ok=True)
        raise

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-sha", default=None)
    args = parser.parse_args()
    try:
        result = build(args.output, source_sha=args.source_sha)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        parser.exit(1, "HAMAPP_SERVICE_KIT_REFUSED: " + type(exc).__name__ + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
