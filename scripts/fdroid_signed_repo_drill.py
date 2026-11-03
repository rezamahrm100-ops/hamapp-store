#!/usr/bin/env python3
"""End-to-end REAL signed F-Droid index drill, disposable GitHub-hosted runner ONLY.

Builds a signed index with fdroidserver, verifies it using the upstream client
library over localhost, and checks wrong signer + mutated index are rejected.
Signing key and config live ONLY inside a TemporaryDirectory. They are never
used for production, backed up, uploaded, registered or published.
"""
import argparse
import hashlib
from functools import partial
import http.server
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import threading
from urllib.parse import urlsplit
import zipfile

HEX64 = re.compile(r"[0-9A-Fa-f]{64}\Z")


class DrillError(RuntimeError):
    pass


class SilentHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return


def run(cmd, *, cwd, env, timeout=180):
    process = subprocess.run(
        cmd, cwd=str(cwd), env=env, capture_output=True, text=True,
        timeout=timeout, check=False)
    if process.returncode:
        # Emit only bounded diagnostic lines; never leak generated private
        # passwords from fdroid init/config to public Actions logs.
        import re
        patterns = re.compile(r"(error|exception|traceback|failed|missing|not found|invalid|no such|warning)", re.I)
        sensitive = re.compile(r"(pass(word)?|secret|credential|token|keystorepass|keypass)", re.I)
        diagnostic = [
            line.strip()[:250] for line in (process.stderr + "\n" + process.stdout).splitlines()
            if patterns.search(line) and not sensitive.search(line)
        ][-7:]
        raise DrillError(f"{cmd[0]} {cmd[1]} failed (exit {process.returncode}); "
                         + " | ".join(diagnostic))


def certified_fingerprint(index_jar):
    from fdroidserver.index import get_public_key_from_jar
    with zipfile.ZipFile(index_jar) as jar:
        _key, fingerprint = get_public_key_from_jar(jar)
    fingerprint = re.sub(r"[^0-9a-fA-F]", "", str(fingerprint)).upper()
    if not HEX64.fullmatch(fingerprint):
        raise DrillError("upstream jar certificate fingerprint invalid")
    return fingerprint


def classify_result(index, expected_id):
    if not isinstance(index, dict):
        raise DrillError("upstream returned no signed index-v2")
    if not isinstance(index.get("repo"), dict) or not isinstance(index.get("packages"), dict):
        raise DrillError("signed index is missing repo/packages")
    if expected_id not in index["packages"]:
        raise DrillError("signed index did not list the actual test APK package")
    return {"indexed_packages": len(index["packages"]), "expected_package_listed": True}


def public_receipt(sha, fp, result, wrong_key_refused, modified_index_refused):
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise DrillError("source SHA not pinned")
    if not HEX64.fullmatch(fp) or not isinstance(result, dict):
        raise DrillError("invalid test evidence")
    if wrong_key_refused is not True or modified_index_refused is not True:
        raise DrillError("negative signature-verification gates did not hold")
    return {
        "schema_version": 1,
        "scope": "isolated-ephemeral-local-F-Droid-signed-index-v2-drill",
        "source_commit": sha,
        "upstream": "fdroidserver init/update/index.download_repo_index_v2",
        "temporary_repo_key_created": True,
        "temporary_key_is_production": False,
        "signed_index_verified_with_temporary_fingerprint": True,
        "wrong_fingerprint_rejected": wrong_key_refused,
        "tampered_index_rejected": modified_index_refused,
        **result,
        "temporary_fingerprint_for_audit_only": fp,
        "production_repo_key_created": False,
        "production_repo_index_signed": False,
        "production_publication_performed": False,
        "approved_app_installed_or_updated": False,
        "production_ready": False
    }


def execute(apk, *, sha):
    if os.name == "nt":
        raise DrillError("signed repo drill requires isolated hosted Linux")
    apk = Path(apk).resolve(strict=True)
    if apk.suffix.lower() != ".apk" or apk.is_symlink() or not apk.is_file():
        raise DrillError("a real debug APK file is required")
    if not 1000 <= apk.stat().st_size < 200 * 1024 * 1024:
        raise DrillError("APK outside expected test bounds")
    from fdroidserver.index import download_repo_index_v2

    with tempfile.TemporaryDirectory(prefix="hamapp-fdroid-throwaway-") as directory:
        base = Path(directory)
        webroot = base / "www"
        workspace = webroot / "fdroid"
        homedir = base / "home"
        workspace.mkdir(parents=True)
        homedir.mkdir()
        env = os.environ.copy()
        env.update({
            "HOME": str(homedir),
            "CI": "true",
            "GIT_TERMINAL_PROMPT": "0",
            "PYTHONUNBUFFERED": "1",
            "NO_PROXY": "127.0.0.1,localhost",
            "no_proxy": "127.0.0.1,localhost",
        })
        handler = partial(SilentHandler, directory=str(webroot))
        with http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
            server.daemon_threads = True
            port = server.server_address[1]
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                run(["fdroid", "init"], cwd=workspace, env=env, timeout=180)
                config_path = workspace / "config.yml"
                if not config_path.is_file() or config_path.is_symlink():
                    raise DrillError("fdroid init did not create private config")
                if config_path.stat().st_mode & 0o077:
                    raise DrillError("temporary signing config must not be group/world readable")
                import yaml
                config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
                if not isinstance(config, dict):
                    raise DrillError("fdroid init generated malformed config")
                config["repo_url"] = f"http://127.0.0.1:{port}/fdroid/repo"
                config["repo_name"] = "Disposable HamApp signature test; NEVER publish"
                config["repo_description"] = "Ephemeral CI proof only; no approved publisher."
                config["include_dns_lookups"] = False
                config_path.write_text(
                    yaml.safe_dump(config, allow_unicode=True, sort_keys=True),
                    encoding="utf-8")
                config_path.chmod(0o600)
                repodir = workspace / "repo"
                repodir.mkdir(exist_ok=True)
                shutil.copyfile(apk, repodir / "app-debug.apk")
                run(["fdroid", "update", "--create-metadata"],
                    cwd=workspace, env=env, timeout=300)
                entry = repodir / "entry.jar"
                index_path = repodir / "index-v2.json"
                if not entry.is_file() or not index_path.is_file():
                    raise DrillError("official fdroid update failed to create signed index-v2")
                fp = certified_fingerprint(entry)
                # The official index verifier uses fdroidserver.common.config
                # for the jarsigner executable. Unlike the fdroid CLI, a
                # direct Python library call must initialize this config.
                from fdroidserver import common
                previous_cwd = Path.cwd()
                try:
                    os.chdir(workspace)
                    common.config = common.read_config()
                finally:
                    os.chdir(previous_cwd)
                if not isinstance(common.config, dict) or not common.config.get("jarsigner"):
                    raise DrillError("upstream jarsigner configuration unavailable")
                url = f"http://127.0.0.1:{port}/fdroid/repo/?fingerprint={fp}"
                data, _etag = download_repo_index_v2(
                    url, verify_fingerprint=True, timeout=30)
                detail = classify_result(data, "ir.hamapp.store")
                # Second independent path: verify the *local* signed entry.jar,
                # its committed index-v2 SHA256, and the exact binary identity.
                from publisher_gate import AAPT
                from verify_fdroid_private_stage import verify as verify_local_index
                badging = subprocess.run(["aapt", "dump", "badging", str(apk)],
                                         capture_output=True, text=True, timeout=40, check=False)
                match = AAPT.search(badging.stdout) if badging.returncode == 0 else None
                if not match or match.group(1) != "ir.hamapp.store":
                    raise DrillError("actual APK manifest identity unavailable")
                version_code = int(match.group(2))
                version_name = match.group(3)
                from urllib.parse import quote
                quoted_version = quote(version_name, safe="-._")
                signed_candidate = {
                    "release": {
                        "app_id": "hamapp-store", "platform": "android",
                        "version": version_name,
                        "asset_url": ("https://github.com/rezamahrm100-ops/hamapp-store/"
                                      "releases/download/v" + quoted_version + "/app-debug.apk"),
                        "sha256": hashlib.sha256(apk.read_bytes()).hexdigest(),
                        "size_bytes": apk.stat().st_size,
                    },
                    "source_repo": "hamapp-store", "source_sha": sha,
                    "package_id": "ir.hamapp.store", "version_code": version_code,
                }
                independent_local = verify_local_index(workspace, fp, signed_candidate)
                if (independent_local["local_index_signed_with_pinned_repository_key"] is not True
                        or independent_local["indexed_apk_sha256"] != signed_candidate["release"]["sha256"]):
                    raise DrillError("independent private index signing and exact APK verification failed")
                detail["local_signed_index_v2_exact_apk_verified"] = True
                other = "B" * 64 if fp != "B" * 64 else "A" * 64
                wrong_key_refused = False
                try:
                    download_repo_index_v2(
                        url.replace(fp, other), verify_fingerprint=True, timeout=30)
                except Exception:
                    wrong_key_refused = True
                original_index = index_path.read_bytes()
                if len(original_index) < 10:
                    raise DrillError("generated index-v2 is implausibly short")
                tampered_index_refused = False
                try:
                    index_path.write_bytes(original_index + b"\nmodified-without-signing")
                    try:
                        download_repo_index_v2(url, verify_fingerprint=True, timeout=30)
                    except Exception:
                        tampered_index_refused = True
                finally:
                    index_path.write_bytes(original_index)
                return public_receipt(sha, fp, detail, wrong_key_refused, tampered_index_refused)
            finally:
                server.shutdown()
                thread.join(timeout=8)


def main():
    parser = argparse.ArgumentParser(description="Isolated, throwaway real F-Droid signed-index verification")
    parser.add_argument("--apk", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.receipt.is_symlink() or args.receipt.exists():
            raise DrillError("receipt cannot be overwritten")
        result = execute(args.apk, sha=args.source_sha)
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, ValueError, DrillError, subprocess.TimeoutExpired, ImportError) as exc:
        parser.exit(1, "FDROID_THROWAWAY_DRILL_FAILED: " + str(exc) + "\n")
    print("EPHEMERAL_SIGNED_INDEX_VERIFIED; WRONG_KEY_AND_TAMPERING_REJECTED; NOT_PRODUCTION")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
