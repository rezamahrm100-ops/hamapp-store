#!/usr/bin/env python3
"""A UI-neutral, fail-closed read model for HamApp's existing upstream engines.

This contract is descriptive, not an authorization token. Windows operations
must still pass windows_client.core; Android installation belongs to the
embedded signed-index verifier and OS PackageInstaller; web is separate.
"""
import argparse
import hashlib
import json
from pathlib import Path

import build_android_catalog
import build_windows_client_catalog
import validate_catalog

ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILES = (
    "apps.json", "trusted_signers.json", "release_history.json",
    "android_repository.json", "winget_packages.json",
    "trusted_web_origins.json", "web_release_history.json",
)


def read_sources(root=ROOT):
    root = Path(root)
    return {
        key.removesuffix(".json"): json.loads((root / "catalog" / key).read_text(encoding="utf-8"))
        for key in SOURCE_FILES
    }


def build(sources):
    """Project approved metadata into a platform-neutral UI action registry.

    No installed-state, user permission, binary signature, or production
    readiness is inferred. All action flags default to False.
    """
    if set(sources) != {name.removesuffix(".json") for name in SOURCE_FILES}:
        raise ValueError("missing or unknown source for UI backend contract")
    catalog = sources["apps"]
    registry = sources["trusted_signers"]
    history = sources["release_history"]
    problems = validate_catalog.validate(
        catalog, registry=registry, history=history,
        web_origins=sources["trusted_web_origins"],
        web_releases=sources["web_release_history"],
    )
    if problems:
        raise ValueError("source approval failed: " + "; ".join(problems))
    android_apps, android_repo = build_android_catalog.build(
        catalog, registry, history, sources["android_repository"]
    )
    windows_apps = build_windows_client_catalog.build(
        catalog, registry, history, sources["winget_packages"]
    )
    android_by_id = {app["id"]: app for app in android_apps["apps"]}
    windows_by_id = {app["id"]: app for app in windows_apps["apps"]}
    result = []
    for app in catalog["apps"]:
        targets = {}
        for platform in app["platforms"]:
            if platform == "android":
                available = (android_by_id[app["id"]]["status"] == "available"
                             and android_repo["repository"] is not None)
                targets[platform] = {
                    "backend": "embedded-fdroid-native",
                    "action": "browse_verified_repository",
                    "enabled": bool(available),
                    "requires_user_consent": True,
                    "repository": android_repo["repository"] if available else None,
                }
            elif platform == "windows":
                entry = windows_by_id[app["id"]]
                available = entry["status"] == "available"
                targets[platform] = {
                    "backend": "microsoft-winget",
                    "action": "request_interactive_operation",
                    "enabled": bool(available),
                    "requires_user_consent": True,
                    "package_id": entry["winget_id"] if available else None,
                    "version": entry["version"] if available else None,
                }
            elif platform == "web":
                available = app["status"] == "released"
                targets[platform] = {
                    "backend": "verified-https-origin",
                    "action": "open_approved_web_release",
                    "enabled": bool(available),
                    "requires_user_consent": True,
                    "url": app["download_url"] if available else None,
                }
            else:
                raise ValueError("unsupported platform")
        result.append({
            "id": app["id"],
            "name_fa": app["name_fa"],
            "name_en": app["name_en"],
            "description": app["description"],
            "status": app["status"],
            "platforms": targets,
        })
    digest = hashlib.sha256(
        json.dumps(catalog, sort_keys=True, ensure_ascii=False,
                   separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "schema_version": 1,
        "contract": "hamapp-ui-backend-v1",
        "catalog_sha256": digest,
        "engines": {
            "android": {
                "id": "fdroid-index",
                "integration": "embedded-library-and-android-os-installer",
                "repository_configured": android_repo["repository"] is not None,
            },
            "windows": {
                "id": "winget",
                "integration": "native-interactive-cli",
                "approved_packages": sum(
                    entry["status"] == "available" for entry in windows_apps["apps"]
                ),
            },
            "web": {
                "id": "browser",
                "integration": "approved-https-origin",
            },
        },
        "apps": result,
    }


def dumps(contract):
    return json.dumps(contract, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write_contract(destination, root=ROOT):
    contract = build(read_sources(root))
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps(contract), encoding="utf-8")
    return contract


def main():
    parser = argparse.ArgumentParser(description="Produce immutable, UI-neutral approved engine metadata")
    parser.add_argument("--output", type=Path, default=ROOT / "dist/ui-contract/store-capabilities.json")
    args = parser.parse_args()
    contract = write_contract(args.output)
    enabled = sum(item["enabled"] for app in contract["apps"]
                  for item in app["platforms"].values())
    print("HamApp UI backend contract:", len(contract["apps"]), "apps,",
          enabled, "approved actions; no installation performed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
