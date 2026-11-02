#!/usr/bin/env python3
"""Reproducible static-site evidence ZIP. Not a package signature or release approval."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import zipfile

FIXED_DATE = (1980, 1, 1, 0, 0, 0)
SOURCE_ROOT = Path(__file__).resolve().parents[1]


def archive_site(site_dir, dest):
    site_dir = Path(site_dir).resolve(strict=True)
    dest = Path(dest).resolve()
    if dest == site_dir or site_dir in dest.parents:
        raise ValueError("archive destination must be outside site directory")
    if not site_dir.is_dir():
        raise ValueError("site path is not a directory")
    files = sorted((p for p in site_dir.rglob("*") if p.is_file()),
                   key=lambda p: p.relative_to(site_dir).as_posix())
    required = {"index.html", "catalog/apps.json", "app.js", "sw.js"}
    names = {p.relative_to(site_dir).as_posix() for p in files}
    if not required.issubset(names):
        raise ValueError("site build misses mandatory assets")
    if any(p.is_symlink() for p in site_dir.rglob("*")):
        raise ValueError("site must contain no symlinks")
    if len(files) > 5000:
        raise ValueError("unreasonably large website tree")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9, allowZip64=True) as output:
        for p in files:
            if not stat.S_ISREG(p.stat().st_mode):
                raise ValueError("site contains a non-regular file")
            name = p.relative_to(site_dir).as_posix()
            info = zipfile.ZipInfo(filename=name, date_time=FIXED_DATE)
            info.create_system = 3
            info.external_attr = (0o100644 << 16)
            info.compress_type = zipfile.ZIP_DEFLATED
            output.writestr(info, p.read_bytes(), compress_type=zipfile.ZIP_DEFLATED,
                            compresslevel=9)
    return len(files)


def evidence(site_dir, output_dir, sha):
    output_dir = Path(output_dir)
    out = output_dir / "hamapp-static-site.zip"
    count = archive_site(site_dir, out)
    digest = hashlib.file_digest(out.open("rb"), "sha256").hexdigest()
    receipt = {
        "schema_version": 1,
        "subject": "HamApp static PWA storefront ZIP (not an Android/Windows app)",
        "source_commit": sha if re.fullmatch(r"[0-9a-f]{40}", sha) else "unverified-local-build",
        "artifact": out.name,
        "sha256": digest,
        "size_bytes": out.stat().st_size,
        "archived_files": count,
        "verified": ["static-build-assets-present", "deterministic-file-order-and-timestamps"],
        "not_verified": [
            "APK signing certificate",
            "Windows Authenticode publisher identity",
            "real-device install or update",
            "F-Droid production signing key",
            "publisher authorization",
            "source-to-binary provenance for external apps",
        ],
        "production_store_ready": False,
    }
    (output_dir / "static-site-evidence.json").write_text(
        json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8")
    return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", type=Path, default=SOURCE_ROOT / "dist/site")
    parser.add_argument("--output", type=Path, default=SOURCE_ROOT / "dist/evidence")
    args = parser.parse_args()
    receipt = evidence(args.site, args.output, os.environ.get("GITHUB_SHA", "local"))
    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
