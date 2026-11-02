#!/usr/bin/env python3
"""Build static, fail-closed reviewed Windows package catalogue from public data."""
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_catalog

WINGET_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9.-]{2,127}\Z")


def build(catalog, registry, history, winget_map):
    errors = validate_catalog.validate(catalog, registry=registry, history=history)
    if errors:
        raise ValueError("source catalogue invalid: " + "; ".join(errors))
    if not isinstance(winget_map, dict) or set(winget_map) != {"schema_version", "packages"}:
        raise ValueError("invalid winget map")
    if type(winget_map["schema_version"]) is not int or winget_map["schema_version"] != 1:
        raise ValueError("winget map schema version invalid")
    if not isinstance(winget_map["packages"], list):
        raise ValueError("winget packages must be an array")
    reviewed = {}
    for item in winget_map["packages"]:
        if not isinstance(item, dict) or set(item) != {"app_id", "winget_id", "version", "artifact_sha256"}:
            raise ValueError("winget mapping must have exact approved fields")
        app_id, package_id = item["app_id"], item["winget_id"]
        if (not isinstance(app_id, str) or not isinstance(package_id, str)
                or not WINGET_ID.fullmatch(package_id) or "." not in package_id
                or ".." in package_id or package_id.startswith(".")):
            raise ValueError("invalid winget mapping identity")
        if app_id in reviewed:
            raise ValueError("duplicate winget mapping")
        reviewed[app_id] = item
    available = set()
    output = []
    for app in catalog["apps"]:
        if "windows" not in app["platforms"]:
            continue
        approved = app["status"] == "released"
        mapped = reviewed.get(app["id"])
        if approved and mapped:
            proof = app["release_proof"]
            if (mapped["version"] != app["version"]
                    or mapped["artifact_sha256"] != proof["sha256"]):
                raise ValueError("winget identity is not tied to the approved artifact")
            version, package_id, state = app["version"], mapped["winget_id"], "available"
            available.add(app["id"])
        else:
            version, package_id, state = None, None, "planned"
        output.append({"id": app["id"], "name_fa": app["name_fa"], "description": app["description"],
                       "status": state, "version": version, "winget_id": package_id})
    if set(reviewed) != available:
        raise ValueError("winget mapping references nonexistent, unapproved or non-Windows app")
    result = {"schema_version": 1, "apps": output}
    # Import the client's own independent runtime contract into build validation.
    sys.path.insert(0, str(ROOT))
    from windows_client.core import validate_manifest
    validate_manifest(result)
    return result


def main():
    source = ROOT / "catalog"
    with (source / "apps.json").open(encoding="utf-8") as f:
        apps = json.load(f)
    with (source / "trusted_signers.json").open(encoding="utf-8") as f:
        registry = json.load(f)
    with (source / "release_history.json").open(encoding="utf-8") as f:
        history = json.load(f)
    with (source / "winget_packages.json").open(encoding="utf-8") as f:
        mappings = json.load(f)
    payload = build(apps, registry, history, mappings)
    out = ROOT / "dist/windows-client/windows-client-catalog.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Windows catalogue built:", len(payload["apps"]), "entries,",
          sum(v["status"] == "available" for v in payload["apps"]), "approved winget packages")


if __name__ == "__main__":
    main()
