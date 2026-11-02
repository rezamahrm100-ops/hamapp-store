#!/usr/bin/env python3
"""Offline, dependency-free reproducible static PWA build."""
import pathlib
import json
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
    # Offline fallback never carries approved/revoked releases or any download URL.
    source = json.loads((ROOT / "catalog/apps.json").read_text(encoding="utf-8"))
    planned = []
    for item in source["apps"]:
        if item["status"] == "planned":
            planned.append({key: value for key, value in item.items()
                            if key not in {"release_proof", "download_url", "version"}}
                           | {"version": None, "download_url": None})
    snapshot = {"schema_version": 1, "apps": planned}
    (output / "catalog/planned-offline.json").write_text(
        json.dumps(snapshot, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8")
    (output / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Site ready: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
