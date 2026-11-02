"""Read-only approved Windows catalogue and bounded winget invocation policy.

No automatic installs, no privilege escalation and no untrusted URLs.  A
reviewed winget mapping is not a cryptographic verification of an installer.
"""
import json
import subprocess
import re
import sys
from pathlib import Path

from windows_client.installed_state import read_installed_version, numeric_version, StateError

APP_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
WINGET_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9.-]{2,127}\Z")
VERSION = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)(?:-[0-9A-Za-z.-]+)?\Z")


class ClientError(ValueError):
    pass


def default_manifest():
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return root / "windows-client-catalog.json"


def load_manifest(filename=None):
    path = Path(filename) if filename is not None else default_manifest()
    contents = json.loads(path.read_text(encoding="utf-8"))
    validate_manifest(contents)
    return contents


def validate_manifest(data):
    if not isinstance(data, dict) or set(data) != {"schema_version", "apps"}:
        raise ClientError("invalid Windows catalogue structure")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise ClientError("invalid catalogue version")
    apps = data["apps"]
    if not isinstance(apps, list) or len(apps) > 10000:
        raise ClientError("invalid app list")
    ids = set()
    for app in apps:
        if not isinstance(app, dict) or set(app) != {"id", "name_fa", "description", "status", "version", "winget_id"}:
            raise ClientError("invalid app entry")
        identity = app["id"]
        if not isinstance(identity, str) or not APP_ID.fullmatch(identity) or identity in ids:
            raise ClientError("invalid/duplicate application id")
        ids.add(identity)
        for field in ("name_fa", "description"):
            if not isinstance(app[field], str) or not app[field].strip() or len(app[field]) > 800:
                raise ClientError("invalid title or description")
        if app["status"] == "planned":
            if app["version"] is not None or app["winget_id"] is not None:
                raise ClientError("planned software cannot have installer metadata")
        elif app["status"] == "available":
            if (not isinstance(app["version"], str) or not VERSION.fullmatch(app["version"])
                    or not isinstance(app["winget_id"], str) or not WINGET_ID.fullmatch(app["winget_id"])):
                raise ClientError("available app must have approved version and winget id")
            if "." not in app["winget_id"] or app["winget_id"].startswith(".") or ".." in app["winget_id"]:
                raise ClientError("invalid winget package identity")
        else:
            raise ClientError("invalid status")
    return data


def command_for(app, operation):
    if sys.platform != "win32":
        raise ClientError("winget actions require native Windows")
    if operation not in ("install", "upgrade", "show"):
        raise ClientError("unsupported operation")
    validate_manifest({"schema_version": 1, "apps": [app]})
    if app["status"] != "available":
        raise ClientError("software is not approved for installation")
    # Official Microsoft winget package source; interactive installer preserves prompts.
    cmd = ["winget", operation, "--id", app["winget_id"], "--exact", "--source", "winget"]
    if operation in ("install", "upgrade"):
        cmd += ["--version", app["version"], "--interactive"]
    return cmd


def execute_operation(app, operation, runner=subprocess.run, verifier=None):
    """Preflight downgrade guard, interactive WinGet and actual installed-state readback.

    The independent readback comes from a separate WinGet export invocation,
    not the install command's exit code. It still cannot prove Authenticode.
    """
    command = command_for(app, operation)
    query = read_installed_version if verifier is None else verifier
    previous = None
    if operation in ("install", "upgrade"):
        try:
            previous = query(app["winget_id"])
            if previous is not None and numeric_version(app["version"]) < numeric_version(previous):
                raise ClientError("refusing requested package version downgrade")
            if operation == "upgrade" and previous is None:
                raise ClientError("cannot upgrade: package is not confirmed installed")
        except StateError as exc:
            raise ClientError("WinGet preflight cannot verify installed package state") from exc
    try:
        result = runner(command, shell=False, timeout=3600, check=False,
                        creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0))
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ClientError("WinGet unavailable or operation timed out; inspect Windows state") from exc
    if type(result.returncode) is not int or result.returncode != 0:
        raise ClientError("WinGet returned a failure; installed state is not verified")
    verified = False
    registered_version = None
    if operation in ("install", "upgrade"):
        try:
            registered_version = query(app["winget_id"])
            verified = registered_version is not None and (
                numeric_version(registered_version) == numeric_version(app["version"]))
        except StateError as exc:
            raise ClientError("post-operation WinGet readback was invalid") from exc
        if not verified:
            raise ClientError("WinGet exited successfully, but target installed version is not confirmed")
    return {"manager_exit_code": 0, "operation": operation,
            "package_id": app["winget_id"], "requested_version": app["version"],
            "installed_version": registered_version,
            "installed_version_via_winget_export_verified": verified,
            "installer_signature_independently_verified": False}
