#!/usr/bin/env python3
"""Stage an owner-verified Android APK into an EXISTING offline F-Droid workspace.

Uses upstream `fdroid update --create-metadata`. Never creates or exports keys.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from publisher_gate import PublisherError, verify
import release_history


def stage(candidate, registry, apk, workspace, runner=subprocess.run, update_runner=subprocess.run, history=None):
    if history is None:
        history = release_history.load_history(Path(__file__).resolve().parents[1] / 'catalog/release_history.json')
    # Check version floor and revocations before invoking expensive signing tools.
    release_history.check_continuity(candidate, registry, history)
    receipt = verify(candidate, registry, apk, runner=runner)
    if receipt["platform"] != "android":
        raise PublisherError("only Android APKs are supported by F-Droid")
    workspace = Path(workspace).resolve(strict=True)
    root = Path(__file__).resolve().parents[1]
    if workspace == root or root in workspace.parents or workspace in root.parents:
        raise PublisherError("signing workspace must be separate from source checkout")
    if not (workspace / "config.yml").is_file() or (workspace / "config.yml").is_symlink():
        raise PublisherError("existing private F-Droid config.yml required")
    if os.name != "nt" and (workspace / "config.yml").stat().st_mode & 0o077:
        raise PublisherError("F-Droid private config.yml must be mode 0600 or stricter")
    repo_dir = workspace / "repo"
    if repo_dir.is_symlink() or (repo_dir.exists() and not repo_dir.is_dir()):
        raise PublisherError("F-Droid repo directory must not be a symlink or file")
    dest = repo_dir / Path(apk).name
    if Path(apk).suffix.lower() != ".apk" or dest.exists() or dest.is_symlink():
        raise PublisherError("expected a new APK filename")
    # No unaudited shell commands and no signing on GitHub-hosted CI.
    dest.parent.mkdir(exist_ok=True)
    try:
        with dest.open("xb") as output, Path(apk).open("rb") as source:
            shutil.copyfileobj(source, output)
        # Recheck staged bytes after copying (mitigates time-of-check/time-of-use changes).
        from release_integrity import verify_file
        verify_file(candidate["release"], dest)
        completed = update_runner(["fdroid", "update", "--create-metadata"], cwd=str(workspace),
                                  capture_output=True, text=True, timeout=300, check=False)
        if completed.returncode != 0:
            raise PublisherError("upstream fdroid update failed (review private workspace logs locally)")
    except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
        dest.unlink(missing_ok=True)
        raise PublisherError("F-Droid staging failed; staged APK removed") from exc
    # This step does not deploy. Independently inspect the output and verify signed index.
    return {**receipt, "staged_filename": dest.name, "deployed": False, "review_required": True}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--candidate", type=Path, required=True)
    p.add_argument("--artifact", type=Path, required=True)
    p.add_argument("--workspace", type=Path, required=True)
    p.add_argument("--registry", type=Path, default=Path(__file__).resolve().parents[1] / "catalog/trusted_signers.json")
    p.add_argument("--receipt", type=Path, required=True)
    p.add_argument("--history", type=Path, default=Path(__file__).resolve().parents[1] / 'catalog/release_history.json')
    args = p.parse_args()
    try:
        if args.receipt.exists():
            raise PublisherError("receipt already exists")
        candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
        registry = json.loads(args.registry.read_text(encoding="utf-8"))
        receipt = stage(candidate, registry, args.artifact, args.workspace, history=release_history.load_history(args.history))
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        with args.receipt.open("x", encoding="utf-8") as f:
            json.dump(receipt, f, indent=2)
            f.write("\n")
    except (OSError, ValueError, PublisherError) as e:
        p.exit(1, "REJECTED: " + str(e) + "\n")
    print("FDROID_STAGED_NOT_DEPLOYED; REVIEW_REQUIRED")
    return 0

if __name__ == "__main__":
    sys.exit(main())
