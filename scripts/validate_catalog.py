#!/usr/bin/env python3
"""Validate public catalogue; binary download links require owner-reviewed approval."""
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import release_integrity
import release_history
import publisher_gate
import web_release_gate

VALID_PLATFORMS = {"android", "windows", "web"}
PROOF_KEYS = {"sha256", "size_bytes", "certificate_sha256", "source_repo", "package_id", "version_code"}


def check_approved_binary(app, registry, history):
    """Validate listing against a previously independently approved history record.

    This is a static CI guard, NOT an independent cryptographic signature check.
    """
    platforms = app["platforms"]
    if len(platforms) != 1 or platforms[0] not in {"android", "windows"}:
        raise ValueError("released binary listing must identify exactly one platform")
    proof = app.get("release_proof")
    if not isinstance(proof, dict) or set(proof) != PROOF_KEYS:
        raise ValueError("released binary requires exactly six release_proof fields")
    platform = platforms[0]
    manifest = {
        "app_id": app["id"],
        "platform": platform,
        "version": app["version"],
        "asset_url": app["download_url"],
        "sha256": proof["sha256"],
        "size_bytes": proof["size_bytes"],
    }
    release_integrity.validate_manifest(manifest)
    pub = [entry for entry in registry["publishers"]
           if entry["app_id"] == app["id"] and entry["platform"] == platform]
    if len(pub) != 1:
        raise ValueError("download requires exactly one trusted publisher")
    publisher = pub[0]
    if (proof["certificate_sha256"] != publisher["certificate_sha256"]
            or proof["source_repo"] != publisher["source_repo"]
            or proof["package_id"] != publisher["package_id"]):
        raise ValueError("download publisher does not match owner-approved registry")
    if publisher["certificate_sha256"] in history["revoked_signers"]:
        raise ValueError("download signing certificate revoked")
    records = [entry for entry in history["releases"]
               if entry["app_id"] == app["id"] and entry["platform"] == platform]
    if not records:
        raise ValueError("no previously approved release history")
    newest = max(records, key=lambda x: (release_history.semver_key(x["version"]),
                                         x["version_code"] if platform == "android" else 0))
    if newest["status"] != "approved":
        raise ValueError("newest release revoked")
    if (newest["version"] != app["version"]
            or newest["artifact_sha256"] != proof["sha256"]
            or newest["certificate_sha256"] != proof["certificate_sha256"]
            or newest["source_repo"] != proof["source_repo"]
            or newest["package_id"] != proof["package_id"]
            or newest["version_code"] != proof["version_code"]):
        raise ValueError("download does not match newest approved release")
    # This check ensures the download origin matches the approved source repository.
    if "/"+proof["source_repo"]+"/releases/download/" not in app["download_url"]:
        raise ValueError("download URL does not match approved source repository")


def validate(data, registry=None, history=None, web_origins=None, web_releases=None):
    errors = []
    if not isinstance(data, dict):
        return ["catalogue must be an object"]
    if registry is None:
        try:
            registry = json.loads((ROOT / "catalog/trusted_signers.json").read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            return ["trusted signer registry unavailable: " + str(exc)]
    if history is None:
        try:
            history = json.loads((ROOT / "catalog/release_history.json").read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            return ["release history unavailable: " + str(exc)]
    if web_origins is None:
        try:
            web_origins = json.loads((ROOT / "catalog/trusted_web_origins.json").read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            return ["trusted web origins unavailable: " + str(exc)]
    if web_releases is None:
        try:
            web_releases = json.loads((ROOT / "catalog/web_release_history.json").read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            return ["web release history unavailable: " + str(exc)]
    try:
        publisher_gate.validate_trust_registry(registry)
        release_history.validate_history(history)
        web_release_gate.validate_origins(web_origins)
        web_release_gate.validate_releases(web_releases)
    except (ValueError, TypeError, KeyError) as exc:
        return ["invalid release trust metadata: " + str(exc)]
    if type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        errors.append("schema_version must be 1")
    apps = data.get("apps")
    if not isinstance(apps, list):
        return errors + ["apps must be an array"]
    ids = set()
    for i, app in enumerate(apps):
        ref = f"apps[{i}]"
        if not isinstance(app, dict):
            errors.append(ref + ": not an object")
            continue
        app_id = app.get("id")
        if not isinstance(app_id, str) or not release_integrity.ID.fullmatch(app_id):
            errors.append(ref + ": invalid app ID")
            continue
        if app_id in ids:
            errors.append(ref + ": duplicated app ID")
        ids.add(app_id)
        for field in ("name_fa", "name_en", "description"):
            value = app.get(field)
            if not isinstance(value, str) or not value.strip() or len(value) > 800:
                errors.append(ref + ": invalid " + field)
        platforms = app.get("platforms")
        if not isinstance(platforms, list) or not platforms or any(p not in VALID_PLATFORMS for p in platforms) or len(set(platforms)) != len(platforms):
            errors.append(ref + ": invalid platforms")
            continue
        state = app.get("status")
        if "changelog" in app:
            changes = app["changelog"]
            if (state != "released" or not isinstance(changes, str)
                    or not changes.strip() or len(changes) > 2000):
                errors.append(ref + ": changelog is allowed only for released apps (max 2000 chars)")
        if state == "planned":
            if (app.get("version") is not None or app.get("download_url") is not None
                    or app.get("release_proof") is not None):
                errors.append(ref + ": planned apps cannot advertise a binary")
        elif state == "released":
            try:
                if platforms == ["web"]:
                    web_release_gate.check_web_release(app, web_origins, web_releases)
                else:
                    check_approved_binary(app, registry, history)
            except (ValueError, TypeError, KeyError, AttributeError) as exc:
                errors.append(ref + ": release approval rejected: " + str(exc))
        else:
            errors.append(ref + ": invalid status")
    return errors


def main():
    try:
        data = json.loads((ROOT / "catalog/apps.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print("Invalid catalogue: " + str(exc), file=sys.stderr)
        return 1
    errors = validate(data)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Catalog validation passed ({len(data['apps'])} apps, approved release gate enabled)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
