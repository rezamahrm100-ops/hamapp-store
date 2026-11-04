"""Read-back of an installed package's version using OFFICIAL WinGet JSON export.

The export is machine-local and immediately deleted; no app inventory,
identifiers or installed programs are uploaded. Exact match only. This reports
WinGet's registered state, not independently verified Authenticode signatures.
"""
import json
from pathlib import Path
import re
import subprocess
import tempfile

INSTALLED_VERSION = re.compile(r"[0-9]+(?:\.[0-9]+){2,3}\Z")


class StateError(ValueError):
    pass


def numeric_version(value):
    if not isinstance(value, str) or not INSTALLED_VERSION.fullmatch(value):
        raise StateError("installed version is not safely comparable; manual review required")
    parts = tuple(int(x) for x in value.split("."))
    return parts + (0,) * (4 - len(parts))


def parse_export(payload, package_id):
    if not isinstance(payload, dict) or not isinstance(payload.get("Sources"), list):
        raise StateError("invalid WinGet export format")
    found = []
    for source in payload["Sources"]:
        if not isinstance(source, dict) or not isinstance(source.get("Packages"), list):
            raise StateError("invalid WinGet source block")
        details = source.get("SourceDetails")
        if not isinstance(details, dict):
            raise StateError("WinGet export source identity missing")
        if str(details.get("Name", "")).lower() != "winget":
            continue
        for item in source["Packages"]:
            if not isinstance(item, dict):
                raise StateError("invalid WinGet package record")
            if item.get("PackageIdentifier") == package_id:
                value = item.get("Version")
                numeric_version(value)
                found.append(value)
    if len(found) > 1:
        raise StateError("ambiguous installed package identity in WinGet export")
    return found[0] if found else None


def _read_official_export(runner):
    """Private temporary WinGet JSON; never uploaded or retained."""
    with tempfile.TemporaryDirectory(prefix="hamapp-winget-state-") as temporary:
        output = Path(temporary) / "installed.json"
        command = ["winget", "export", "--source", "winget",
                   "--output", str(output), "--include-versions",
                   "--disable-interactivity"]
        try:
            result = runner(command, shell=False, capture_output=True, text=True,
                            timeout=180, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise StateError("WinGet installed-state query unavailable") from exc
        if result.returncode != 0 or not output.is_file() or output.is_symlink():
            raise StateError("WinGet did not produce a valid installed-state export")
        if not 0 < output.stat().st_size <= 8_000_000:
            raise StateError("WinGet installed-state export is empty or oversized")
        try:
            return json.loads(output.read_text(encoding="utf-8-sig"))
        except (UnicodeError, ValueError, OSError) as exc:
            raise StateError("WinGet installed-state export has malformed JSON") from exc


def parse_installed_inventory(payload):
    """Only exact source-tagged WinGet IDs with comparable installed versions.

    This is read-only machine-local inventory; not evidence that HamApp
    approved these publishers or independently verified installer signatures.
    """
    if not isinstance(payload, dict) or not isinstance(payload.get("Sources"), list):
        raise StateError("invalid WinGet inventory export")
    found = {}
    for source in payload["Sources"]:
        if not isinstance(source, dict) or not isinstance(source.get("Packages"), list):
            raise StateError("invalid WinGet inventory source block")
        details = source.get("SourceDetails")
        if not isinstance(details, dict):
            raise StateError("WinGet export source identity missing")
        if details.get("Name", "").lower() != "winget":
            continue
        for entry in source["Packages"]:
            if not isinstance(entry, dict):
                raise StateError("invalid WinGet inventory package record")
            key, version = entry.get("PackageIdentifier"), entry.get("Version")
            if not isinstance(key, str) or not re.fullmatch(
                    r"[A-Za-z0-9][A-Za-z0-9.-]{2,127}", key) or "." not in key or ".." in key:
                raise StateError("invalid WinGet inventory package identity")
            numeric_version(version)
            if key in found:
                raise StateError("ambiguous WinGet inventory identity")
            found[key] = version
            if len(found) > 500:
                raise StateError("oversized WinGet inventory")
    return [{"id": key, "version": found[key], "source": "winget"}
            for key in sorted(found, key=str.casefold)]


def read_installed_inventory(runner=subprocess.run):
    return parse_installed_inventory(_read_official_export(runner))


def read_installed_version(package_id, runner=subprocess.run):
    # Caller validates exact package ID before reaching this function.
    return parse_export(_read_official_export(runner), package_id)
