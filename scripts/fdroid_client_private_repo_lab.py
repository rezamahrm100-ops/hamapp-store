#!/usr/bin/env python3
"""Prepare and rotate a REAL signed test-only F-Droid HTTP repo for Android emulator.

The disposable fdroidserver keystore/config are ALWAYS outside the served
HTTP directory, in RUNNER_TEMP only. Only signed repo files and real APKs
can be served over emulator's 10.0.2.2 loopback; no owner/public credentials.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess

from fdroid_signed_repo_drill import certified_fingerprint, run, DrillError
from verify_fdroid_private_stage import verify as verify_signed_repo
from publisher_gate import AAPT

PORT = 8975
REPO_URL = f"http://10.0.2.2:{PORT}/fdroid/repo/"
LAB = "hamapp-fdroid-real-official-client-lab"
ALLOWED = {".apk", ".jar", ".json", ".xml", ".png", ".webp", ".svg"}
SHA40 = re.compile(r"[a-f0-9]{40}\Z")


def root():
    if os.name == "nt" or os.environ.get("GITHUB_ACTIONS") != "true" or os.environ.get("RUNNER_OS") != "Linux":
        raise DrillError("isolated GitHub-hosted Linux F-Droid lab only")
    temp = os.environ.get("RUNNER_TEMP")
    if not temp:
        raise DrillError("missing hosted temporary directory")
    base = Path(temp).resolve(strict=True) / LAB
    if base.is_symlink():
        raise DrillError("unsafe disposable lab symlink")
    return base


def env_for(base):
    env = os.environ.copy()
    env.update({"HOME": str(base / "home"), "CI": "true",
                "GIT_TERMINAL_PROMPT": "0",
                "NO_PROXY": "127.0.0.1,localhost,10.0.2.2",
                "no_proxy": "127.0.0.1,localhost,10.0.2.2"})
    return env


def apk_identity(path):
    file = Path(path)
    if file.is_symlink() or not file.is_file() or not 1000 <= file.stat().st_size < 180 * 1024 * 1024:
        raise DrillError("real signed Android APK required")
    output = subprocess.run(["aapt", "dump", "badging", str(file)],
                            capture_output=True, text=True, timeout=30, check=False)
    match = AAPT.search(output.stdout) if output.returncode == 0 else None
    if not match or match.group(1) != "ir.hamapp.store":
        raise DrillError("real package identity or version unavailable")
    return {"version_code": int(match.group(2)), "version_name": match.group(3),
            "sha256": hashlib.sha256(file.read_bytes()).hexdigest(),
            "size": file.stat().st_size}


def candidate(data, source_sha):
    from urllib.parse import quote
    return {
        "release": {
            "app_id": "hamapp-store", "platform": "android",
            "version": data["version_name"],
            "asset_url": "https://github.com/rezamahrm100-ops/hamapp-store/releases/download/v"
                         + quote(data["version_name"], safe="-._") + "/app-debug.apk",
            "sha256": data["sha256"], "size_bytes": data["size"],
        },
        "source_repo": "hamapp-store",
        "source_sha": source_sha,
        "package_id": "ir.hamapp.store",
        "version_code": data["version_code"]
    }


def publish_files(base):
    """Publish only generated repository files; NEVER config.yml/keystore."""
    private_repo = base / "signing" / "repo"
    public = base / "webroot" / "fdroid" / "repo"
    if public.is_symlink():
        raise DrillError("unsafe public repo destination")
    if public.exists():
        shutil.rmtree(public)
    public.mkdir(parents=True, mode=0o700)
    count = 0
    for path in private_repo.rglob("*"):
        rel = path.relative_to(private_repo)
        if path.is_symlink() or rel.is_absolute() or ".." in rel.parts:
            raise DrillError("unsafe indexed repository artifact")
        output = public / rel
        if path.is_dir():
            output.mkdir(parents=True, exist_ok=True)
            continue
        info = path.stat()
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                or path.suffix.lower() not in ALLOWED
                or info.st_size > 180 * 1024 * 1024):
            raise DrillError("private credential or unsupported file entered public repo")
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, output)
        output.chmod(0o600)
        count += 1
    if count < 4 or not (public / "entry.jar").is_file() or not (public / "index-v2.json").is_file():
        raise DrillError("real generated signed public mirror incomplete")
    # Verify the absolute path containment which protects against mistakenly
    # publishing the full private fdroid signing workspace.
    if (base / "signing" / "config.yml").exists() and (base / "webroot" / "fdroid" / "config.yml").exists():
        raise DrillError("private fdroid configuration leaked into HTTP webroot")
    return count


def stage(version, apk, source_sha):
    if not SHA40.fullmatch(source_sha):
        raise DrillError("immutable GitHub source SHA required")
    base = root()
    private = base / "signing"
    state_path = base / "state.json"
    env = env_for(base)
    if version == 1:
        if base.exists():
            raise DrillError("refuse to reuse disposable lab")
        private.mkdir(parents=True, mode=0o700)
        (base / "home").mkdir(mode=0o700)
        (base / "webroot" / "fdroid").mkdir(parents=True, mode=0o700)
        run(["fdroid", "init"], cwd=private, env=env, timeout=180)
        import yaml
        config_path = private / "config.yml"
        if not config_path.is_file() or config_path.is_symlink():
            raise DrillError("private signing config missing")
        config = yaml.safe_load(config_path.read_text("utf-8"))
        if not isinstance(config, dict):
            raise DrillError("malformed upstream signing configuration")
        config["repo_url"] = REPO_URL.rstrip("/")
        config["repo_name"] = "Disposable HamApp emulator install test only"
        config["repo_description"] = "Not a public signer or approved third-party publisher."
        config["include_dns_lookups"] = False
        config_path.write_text(yaml.safe_dump(config, sort_keys=True), encoding="utf-8")
        config_path.chmod(0o600)
        (private / "repo").mkdir(exist_ok=True)
        state = {"schema_version": 1, "source_sha": source_sha,
                 "real_repo_url": REPO_URL, "versions": []}
    elif version == 2:
        if not base.is_dir() or not state_path.is_file() or state_path.is_symlink():
            raise DrillError("no previous signed v1 repository")
        state = json.loads(state_path.read_text("utf-8"))
        if state.get("source_sha") != source_sha or len(state.get("versions", [])) != 1:
            raise DrillError("missing verified first signed version")
    else:
        raise DrillError("only actual first and second versions supported")
    apk = Path(apk).resolve(strict=True)
    info = apk_identity(apk)
    if info["version_code"] != version:
        raise DrillError("unexpected real Android build version code")
    if version == 2:
        if info["sha256"] == state["versions"][0]["sha256"]:
            raise DrillError("second APK must differ")
        if certified_fingerprint(private / "repo" / "entry.jar") != state["fingerprint"]:
            raise DrillError("test repo signer changed before v2")
    copied = private / "repo" / f"hamapp-v{version}.apk"
    if copied.exists() or copied.is_symlink():
        raise DrillError("real APK version already staged")
    shutil.copyfile(apk, copied)
    run(["fdroid", "update", "--create-metadata"], cwd=private, env=env, timeout=300)
    # Official fdroidserver.index.get_index_from_jar requires the upstream
    # jarsigner config initialized explicitly for direct Python API calls.
    # fdroid CLI itself does this, but the imported library does not.
    from fdroidserver import common
    previous = Path.cwd()
    try:
        os.chdir(private)
        common.config = common.read_config()
    finally:
        os.chdir(previous)
    if not isinstance(common.config, dict) or not common.config.get("jarsigner"):
        raise DrillError("upstream F-Droid JAR verifier has no actual jarsigner config")
    fingerprint = certified_fingerprint(private / "repo" / "entry.jar")
    if version == 1:
        state["fingerprint"] = fingerprint
    elif fingerprint != state["fingerprint"]:
        raise DrillError("signed repo key changed across actual indexes")
    for prior in state["versions"] + [info]:
        receipt = verify_signed_repo(private, fingerprint, candidate(prior, source_sha))
        if not receipt["local_index_signed_with_pinned_repository_key"]:
            raise DrillError("actual upstream signed metadata not verified")
    state["versions"].append(info)
    publish_files(base)
    state_path.write_text(json.dumps(state, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    state_path.chmod(0o600)
    print(f"ACTUAL_SIGNED_TEST_REPO_VERSION_{version}_READY; NOT_OWNER_PRODUCTION")
    return state


def main():
    parser = argparse.ArgumentParser(description="Private real signed F-Droid emulator lab")
    parser.add_argument("--version", type=int, choices=(1, 2), required=True)
    parser.add_argument("--apk", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    a = parser.parse_args()
    try:
        stage(a.version, a.apk, a.source_sha)
    except (OSError, ValueError, TypeError, ImportError, DrillError,
            subprocess.TimeoutExpired) as exc:
        parser.exit(1, "PRIVATE_FDROID_CLIENT_LAB_REFUSED: " + str(exc) + "\n")


if __name__ == "__main__":
    main()
