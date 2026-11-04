#!/usr/bin/env python3
"""Inspect ACTUAL APK manifest permissions with official Android SDK aapt.

The reviewed policy is exact package/version/allowed-permission metadata; no
application signing key, code execution inside APK, install or release approval.
Unknown/malformed tool output fails closed. Real CI runs on a DEBUG HamApp APK.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

import publisher_gate

PERMISSION = re.compile(r"android\.permission\.[A-Z0-9_]+\Z")
def permitted_name(value, package_id=None):
    """Only system permissions or our own AndroidX signature receiver guard."""
    return bool(PERMISSION.fullmatch(value)) or (isinstance(package_id, str)
        and value == package_id + ".DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION")


GRANTED_LINE = re.compile(r"^\s*uses-permission(?:-sdk-[0-9]+)?:\s*name='([^']+)'(?:\s.*)?$")
BADGE_LINE = publisher_gate.AAPT


class AndroidPermissionError(ValueError):
    pass


def validate_policy(policy):
    if (not isinstance(policy, dict) or set(policy) != {
        "schema_version", "package_id", "version_code", "version_name", "allowed_permissions"
    } or type(policy["schema_version"]) is not int or policy["schema_version"] != 1):
        raise AndroidPermissionError("invalid Android permission policy schema")
    if (not isinstance(policy["package_id"], str)
            or not publisher_gate.PACKAGE.fullmatch(policy["package_id"])):
        raise AndroidPermissionError("invalid exact Android package identity")
    if (type(policy["version_code"]) is not int
            or not 1 <= policy["version_code"] <= 2**31 - 1):
        raise AndroidPermissionError("invalid Android versionCode")
    if (not isinstance(policy["version_name"], str)
            or not policy["version_name"] or len(policy["version_name"]) > 128):
        raise AndroidPermissionError("invalid Android versionName")
    requested = policy["allowed_permissions"]
    if (not isinstance(requested, list) or len(requested) > 128
            or any(not isinstance(v, str) or not permitted_name(v, policy["package_id"]) for v in requested)
            or len(set(requested)) != len(requested)):
        raise AndroidPermissionError("invalid or duplicate allowlisted permission")
    return policy


def invoke_aapt(aapt, command, apk, runner=subprocess.run):
    cmd = [str(aapt), "dump", command, str(apk)]
    try:
        result = runner(cmd, shell=False, capture_output=True, text=True,
                        timeout=45, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AndroidPermissionError("official Android aapt tool unavailable or timed out") from exc
    if result.returncode != 0 or not isinstance(result.stdout, str) or len(result.stdout) > 500000:
        raise AndroidPermissionError("official Android aapt validation failed")
    return result.stdout


def parse_requested_permissions(stdout, package_id=None):
    if not isinstance(stdout, str):
        raise AndroidPermissionError("invalid manifest permission output")
    found = set()
    for raw in stdout.splitlines():
        stripped = raw.strip()
        if stripped.startswith(("uses-permission", "implied-permission")):
            match = GRANTED_LINE.fullmatch(raw)
            if not match or not permitted_name(match.group(1), package_id):
                raise AndroidPermissionError("unknown or malformed manifest permission declaration")
            if match.group(1) in found:
                raise AndroidPermissionError("duplicate APK permission declaration")
            found.add(match.group(1))
    return sorted(found)


def review(apk, policy, aapt="aapt", runner=subprocess.run):
    validate_policy(policy)
    apk = Path(apk)
    if apk.is_symlink() or not apk.is_file() or apk.suffix.lower() != ".apk":
        raise AndroidPermissionError("expected actual non-symlink APK")
    total = apk.stat().st_size
    if not 0 < total <= 2 * 1024**3:
        raise AndroidPermissionError("APK missing or unreasonably sized")
    digest = hashlib.sha256()
    with apk.open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(data)
    badges = invoke_aapt(aapt, "badging", apk, runner=runner)
    match = BADGE_LINE.search(badges)
    if not match or (match.group(1), int(match.group(2)), match.group(3)) != (
            policy["package_id"], policy["version_code"], policy["version_name"]):
        raise AndroidPermissionError("actual APK package/version differs from reviewed policy")
    permissions = parse_requested_permissions(
        invoke_aapt(aapt, "permissions", apk, runner=runner), policy["package_id"])
    unknown = sorted(set(permissions) - set(policy["allowed_permissions"]))
    if unknown:
        raise AndroidPermissionError("APK requests permissions absent from reviewed allowlist: " + ", ".join(unknown))
    # This only proves aapt-reported manifest permissions, not dynamic behavior.
    return {
        "schema_version": 1, "package_id": policy["package_id"],
        "version_code": policy["version_code"], "version_name": policy["version_name"],
        "apk_sha256": digest.hexdigest(), "apk_size_bytes": total,
        "requested_permissions": permissions,
        "requested_permissions_allowlist_checked": True,
        "tool": "Android SDK aapt dump permissions + badging",
        "code_signature_verified": False, "malware_free_verified": False,
        "app_permission_runtime_behavior_verified": False,
        "production_release_authorized": False,
    }


def main():
    p = argparse.ArgumentParser(description="Review actual Android manifest permissions, NOT malware clearance")
    p.add_argument("--apk", type=Path, required=True)
    p.add_argument("--policy", type=Path, required=True)
    p.add_argument("--aapt", default="aapt")
    p.add_argument("--receipt", type=Path, required=True)
    args = p.parse_args()
    try:
        if args.receipt.is_symlink() or args.receipt.exists():
            raise AndroidPermissionError("refusing to overwrite an existing receipt")
        policy = json.loads(args.policy.read_text(encoding="utf-8"))
        result = review(args.apk, policy, aapt=args.aapt)
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        with args.receipt.open("x", encoding="utf-8") as file:
            json.dump(result, file, ensure_ascii=False, indent=2, sort_keys=True)
            file.write("\n")
    except (ValueError, OSError, TypeError) as exc:
        p.exit(1, "APK_PERMISSION_REJECTED: " + str(exc) + "\n")
    print("APK_MANIFEST_PERMISSIONS_REVIEWED; NO_MALWARE_OR_RELEASE_APPROVAL")


if __name__ == "__main__":
    main()
