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


def read_installed_version(package_id, runner=subprocess.run):
    # Caller must validate approved package ID before reaching this function.
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
            data = json.loads(output.read_text(encoding="utf-8-sig"))
        except (UnicodeError, ValueError, OSError) as exc:
            raise StateError("WinGet installed-state export has malformed JSON") from exc
        return parse_export(data, package_id)
