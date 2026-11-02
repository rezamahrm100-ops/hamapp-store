#!/usr/bin/env python3
"""Offline, dependency-free reproducible static PWA build."""
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_catalog  # noqa: E402


def main():
    if validate_catalog.main() != 0:
        return 1
    output = ROOT / "dist" / "site"
    if output.exists():
        shutil.rmtree(output)
    shutil.copytree(ROOT / "web", output)
    shutil.copytree(ROOT / "catalog", output / "catalog")
    (output / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Site ready: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
