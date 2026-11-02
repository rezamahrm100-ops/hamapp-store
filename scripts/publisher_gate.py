#!/usr/bin/env python3
"""Fail-closed verification of release candidates against owner-pinned signer identities.

No network access, no secret handling, no automatic public release. External tools:
Android: apksigner + aapt. Windows: PowerShell Get-AuthenticodeSignature.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import release_integrity

SHA = re.compile(r"[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
PACKAGE = re.compile(r"[a-zA-Z][a-zA-Z0-9_]*(?:\.[a-zA-Z][a-zA-Z0-9_]*)+\Z")
APK_SIGNER = re.compile(r"^Signer #(\d+) certificate SHA-256 digest:\s*([0-9a-fA-F:]{64,95})\s*$", re.M)
AAPT = re.compile(r"^package:\s+name='([^']+)'\s+versionCode='([0-9]+)'\s+versionName='([^']+)'", re.M)
OWNER = "rezamahrm100-ops"

class PublisherError(ValueError):
    pass


def normalize_fingerprint(value):
    if not isinstance(value, str):
        raise PublisherError("fingerprint must be a string")
    fp = value.replace(":", "").lower()
    if not SHA.fullmatch(fp):
        raise PublisherError("invalid SHA-256 signing certificate fingerprint")
    return fp


def validate_trust_registry(registry):
    if not isinstance(registry, dict) or set(registry) != {"schema_version", "publishers"} or registry["schema_version"] != 1 or not isinstance(registry["publishers"], list):
        raise PublisherError("invalid trust registry")
    seen = set()
    for p in registry["publishers"]:
        if not isinstance(p, dict) or set(p) != {"app_id", "source_repo", "platform", "certificate_sha256", "package_id"}:
            raise PublisherError("invalid publisher schema")
        app_id = p["app_id"]
        if not isinstance(app_id, str) or not release_integrity.ID.fullmatch(app_id) or app_id in seen:
            raise PublisherError("invalid/duplicate app_id")
        seen.add(app_id)
        if not isinstance(p["source_repo"], str) or not release_integrity.ID.fullmatch(p["source_repo"]):
            raise PublisherError("invalid publisher source repo")
        if p["platform"] not in ("android", "windows"):
            raise PublisherError("invalid platform")
        normalize_fingerprint(p["certificate_sha256"])
        if p["platform"] == "android":
            if not isinstance(p["package_id"], str) or not PACKAGE.fullmatch(p["package_id"]):
                raise PublisherError("invalid Android package id")
        elif p["package_id"] is not None:
            raise PublisherError("Windows package_id must be null")
    return registry


def validate_candidate(candidate, registry):
    validate_trust_registry(registry)
    if not isinstance(candidate, dict) or set(candidate) != {"release", "source_repo", "source_sha", "package_id", "version_code"}:
        raise PublisherError("invalid candidate schema")
    release = release_integrity.validate_manifest(candidate["release"])
    if not isinstance(candidate["source_sha"], str) or not COMMIT.fullmatch(candidate["source_sha"]):
        raise PublisherError("source_sha must be full commit SHA")
    if not isinstance(candidate["source_repo"], str) or not release_integrity.ID.fullmatch(candidate["source_repo"]):
        raise PublisherError("invalid source_repo")
    url_path = release["asset_url"].split("github.com/", 1)[1].split("/releases/download/", 1)[0]
    if url_path != OWNER + "/" + candidate["source_repo"]:
        raise PublisherError("source repository differs from download origin")
    matching = [p for p in registry["publishers"] if p["app_id"] == release["app_id"] and p["platform"] == release["platform"]]
    if len(matching) != 1:
        raise PublisherError("no unique trusted publisher registration")
    pub = matching[0]
    if pub["source_repo"] != candidate["source_repo"] or pub["package_id"] != candidate["package_id"]:
        raise PublisherError("untrusted publisher source or package id")
    if release["platform"] == "android":
        if type(candidate["version_code"]) is not int or not (1 <= candidate["version_code"] <= 2**31 - 1):
            raise PublisherError("invalid Android version_code")
    elif candidate["version_code"] is not None:
        raise PublisherError("Windows version_code must be null")
    return pub


def run_tool(command, timeout=60, runner=subprocess.run):
    try:
        output = runner(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise PublisherError("signature tool unavailable or timed out") from exc
    if output.returncode != 0:
        raise PublisherError("signature tool verification failed")
    if len(output.stdout) > 100_000:
        raise PublisherError("signature output exceeds permitted size")
    return output.stdout


def verify_apk(artifact, package_id, version_code, version_name, runner=subprocess.run):
    raw = run_tool(["apksigner", "verify", "--verbose", "--print-certs", str(artifact)], runner=runner)
    certs = APK_SIGNER.findall(raw)
    if len(certs) != 1 or certs[0][0] != "1":
        raise PublisherError("expected exactly one APK signer")
    fingerprint = normalize_fingerprint(certs[0][1])
    badge = run_tool(["aapt", "dump", "badging", str(artifact)], runner=runner)
    match = AAPT.search(badge)
    if not match or match.group(1) != package_id or int(match.group(2)) != version_code or match.group(3) != version_name:
        raise PublisherError("APK package, versionCode or versionName mismatch")
    return fingerprint


def verify_authenticode(artifact, runner=subprocess.run):
    if os.name != "nt":
        raise PublisherError("Windows signature verification requires native Windows")
    # Powershell -EncodedCommand avoids escaping file paths and PowerShell interpolation.
    script = """$ErrorActionPreference = 'Stop'; $s = Get-AuthenticodeSignature -LiteralPath $args[0];
if ($s.Status -ne 'Valid' -or $null -eq $s.SignerCertificate) { exit 12 }
$sha = [Security.Cryptography.SHA256]::Create();
try { $b = $sha.ComputeHash($s.SignerCertificate.RawData); [BitConverter]::ToString($b).Replace('-', '').ToLowerInvariant() }
finally { $sha.Dispose() }
"""
    # Pass the path as a base64-encoded UTF-16LE literal, never interpolate user data.
    import base64
    path64 = base64.b64encode(str(artifact).encode("utf-16le")).decode("ascii")
    command = script.replace("$args[0]", f"([Text.Encoding]::Unicode.GetString([Convert]::FromBase64String('{path64}')))")
    encoded = base64.b64encode(command.encode("utf-16le")).decode("ascii")
    output = run_tool(["powershell.exe", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded], runner=runner)
    lines = [v.strip() for v in output.splitlines() if v.strip()]
    if len(lines) != 1:
        raise PublisherError("unexpected Windows certificate output")
    return normalize_fingerprint(lines[0])


def verify(candidate, registry, artifact, runner=subprocess.run):
    pub = validate_candidate(candidate, registry)
    receipt = release_integrity.verify_file(candidate["release"], artifact)
    if receipt["platform"] == "android":
        actual = verify_apk(artifact, candidate["package_id"], candidate["version_code"], receipt["version"], runner=runner)
    else:
        actual = verify_authenticode(artifact, runner=runner)
    if actual != normalize_fingerprint(pub["certificate_sha256"]):
        raise PublisherError("signing certificate is not pinned to this publisher")
    return {**receipt, "source_repo": candidate["source_repo"], "source_sha_claimed": candidate["source_sha"],
            "source_commit_verified": False,
            "package_id": candidate["package_id"], "version_code": candidate["version_code"],
            "signer_certificate_sha256": actual, "signature_verified": True,
            "review_required": True, "public_release_authorized": False}


def main():
    parser = argparse.ArgumentParser(description="Verify an allowlisted package; does not authorize publication")
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--registry", type=Path, default=Path(__file__).resolve().parents[1] / "catalog/trusted_signers.json")
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    try:
        candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
        registry = json.loads(args.registry.read_text(encoding="utf-8"))
        verified = verify(candidate, registry, args.artifact)
        if args.receipt.exists() or args.receipt.is_symlink():
            raise PublisherError("refusing to overwrite an existing receipt")
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        with args.receipt.open("x", encoding="utf-8") as out:
            json.dump(verified, out, ensure_ascii=False, indent=2)
            out.write("\n")
    except (PublisherError, release_integrity.IntegrityError, OSError, ValueError, UnicodeError) as exc:
        parser.exit(1, "REJECTED: " + str(exc) + "\n")
    print("PUBLISHER_SIGNATURE_AND_HASH_VERIFIED; HUMAN_REVIEW_REQUIRED")
    return 0

if __name__ == "__main__":
    sys.exit(main())
