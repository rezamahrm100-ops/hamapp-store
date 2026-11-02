#!/usr/bin/env python3
"""Generate offline Android catalogue assets from owner-reviewed public metadata.

F-Droid is the installer; this never downloads APKs, creates keys or publishes.
"""
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_catalog

HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")


def validate_repository(config):
    if not isinstance(config, dict) or set(config) != {"schema_version", "repository"}:
        raise ValueError("invalid repository config structure")
    if type(config["schema_version"]) is not int or config["schema_version"] != 1:
        raise ValueError("invalid repository config version")
    repo = config["repository"]
    if repo is None:
        return None
    if not isinstance(repo, dict) or set(repo) != {"url", "fingerprint"}:
        raise ValueError("repository requires only url and fingerprint")
    url, fp = repo["url"], repo["fingerprint"]
    if not isinstance(url, str) or len(url) > 2048 or any(x in url for x in ("%", "\\", "\r", "\n")):
        raise ValueError("invalid repository URL")
    if not isinstance(fp, str) or not HEX64.fullmatch(fp):
        raise ValueError("invalid repository fingerprint")
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or not parsed.hostname or "." not in parsed.hostname
            or parsed.port is not None or parsed.username or parsed.password
            or parsed.query or parsed.fragment or parsed.path != "/fdroid/repo/"
            or url != "https://" + parsed.hostname.lower() + "/fdroid/repo/"):
        raise ValueError("F-Droid repository must use canonical HTTPS /fdroid/repo/ URL")
    return {"url": url, "fingerprint": fp.upper()}


def build(catalog, registry, history, config):
    errors = validate_catalog.validate(catalog, registry=registry, history=history)
    if errors:
        raise ValueError("catalogue rejected: " + "; ".join(errors))
    repo = validate_repository(config)
    apps = []
    for app in catalog["apps"]:
        if "android" not in app["platforms"]:
            continue
        is_approved = app["status"] == "released"
        available = bool(repo and is_approved)
        apps.append({
            "id": app["id"], "name_fa": app["name_fa"],
            "description": app["description"],
            "status": "available" if available else "planned",
            "version": app["version"] if available else None,
        })
    return {"schema_version": 1, "apps": apps}, {"schema_version": 1, "repository": repo}


def main():
    catalog_dir = ROOT / "catalog"
    def read(filename):
        return json.loads((catalog_dir / filename).read_text(encoding="utf-8"))
    listing, config = build(read("apps.json"), read("trusted_signers.json"),
                            read("release_history.json"), read("android_repository.json"))
    output = ROOT / "android/app/src/main/assets"
    output.mkdir(parents=True, exist_ok=True)
    (output / "android-catalog.json").write_text(
        json.dumps(listing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "android-repository.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Android preview metadata:", len(listing["apps"]), "apps,",
          sum(app["status"] == "available" for app in listing["apps"]), "installable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
