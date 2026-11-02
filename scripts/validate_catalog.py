#!/usr/bin/env python3
"""Fail closed on malformed or incorrectly advertised downloadable app releases."""
import json
import pathlib
import re
import sys
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parents[1]
VALID_PLATFORMS = {"android", "windows", "web"}


def validate(data):
    errors = []
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    apps = data.get("apps")
    if not isinstance(apps, list):
        return ["apps must be an array"]
    seen = set()
    for i, app in enumerate(apps):
        ref = f"apps[{i}]"
        if not isinstance(app, dict):
            errors.append(f"{ref}: not an object")
            continue
        app_id = app.get("id")
        if not isinstance(app_id, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", app_id):
            errors.append(f"{ref}.id must be a kebab-case ascii string")
        if app_id in seen:
            errors.append(f"{ref}.id is duplicated")
        seen.add(app_id)
        for key in ("name_fa", "name_en", "description"):
            if not isinstance(app.get(key), str) or not app[key].strip() or len(app[key]) > 800:
                errors.append(f"{ref}.{key} invalid")
        platforms = app.get("platforms")
        if not isinstance(platforms, list) or not platforms or set(map(str, platforms)) - VALID_PLATFORMS:
            errors.append(f"{ref}.platforms invalid")
        state = app.get("status")
        if state not in {"planned", "released"}:
            errors.append(f"{ref}.status invalid")
        version, download = app.get("version"), app.get("download_url")
        if state == "released":
            if not isinstance(version, str) or not re.fullmatch(r"[0-9]+(?:\.[0-9]+){1,3}(?:[-+][0-9a-zA-Z.-]+)?", version):
                errors.append(f"{ref}.version invalid for released app")
            if not isinstance(download, str) or urlparse(download).scheme != "https" or not urlparse(download).netloc or urlparse(download).username or urlparse(download).password:
                errors.append(f"{ref}.download_url must be HTTPS with no user info")
        elif version is not None or download is not None:
            errors.append(f"{ref}: planned apps must not have a release or download link")
    return errors


def main():
    data = json.loads((ROOT / "catalog/apps.json").read_text(encoding="utf-8"))
    errors = validate(data)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Catalog validation passed ({len(data['apps'])} apps)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
