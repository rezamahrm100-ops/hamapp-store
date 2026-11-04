"""Independent, opt-in third-party WinGet discovery; never marks a HamApp app approved.

The bundled HamApp store catalog remains owner-reviewed and strictly gated in
windows_client.core. WinGet community packages are a distinct third-party
channel, displayed with explicit provenance and per-action consent. No
automatic source/EULA acceptance, silent installation or UAC bypass.
"""
import re
import subprocess
import sys
import unicodedata

from windows_client.installed_state import read_installed_version, read_installed_inventory, numeric_version, StateError

PACKAGE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9.-]{2,127}\Z")
ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
MAX_OUTPUT = 65536


class DiscoveryError(ValueError):
    pass


def _on_windows():
    return sys.platform == "win32"


def checked_id(package_id):
    if (not isinstance(package_id, str) or not PACKAGE_ID.fullmatch(package_id)
            or "." not in package_id or ".." in package_id
            or package_id.startswith(".") or package_id.endswith(".")):
        raise DiscoveryError("invalid WinGet package identifier")
    return package_id


def checked_query(query):
    if (not isinstance(query, str) or not 2 <= len(query.strip()) <= 80
            or query.strip().startswith("-")
            or any(unicodedata.category(ch).startswith("C") for ch in query)):
        raise DiscoveryError("search requires 2–80 printable characters")
    return query.strip()


def _call(args, runner=subprocess.run, timeout=60):
    if not _on_windows():
        raise DiscoveryError("WinGet requires native Windows")
    try:
        result = runner(args, shell=False, capture_output=True, text=True,
                        errors="replace", timeout=timeout, check=False,
                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DiscoveryError("WinGet unavailable or request timed out") from exc
    if result.returncode != 0:
        # Do not infer source-license acceptance or any package installed state.
        raise DiscoveryError("WinGet returned an error. Confirm App Installer and source agreements in Windows.")
    return ANSI_ESCAPE.sub("", (result.stdout or "")[:MAX_OUTPUT])


def search(query, runner=subprocess.run):
    """Search ONLY the official WinGet source; parse conservatively.

    If localized console formatting is not parseable, return raw text without
    actionable identifiers. Exact 'show' preflight is still mandatory.
    """
    term = checked_query(query)
    raw = _call(["winget", "search", "--query", term, "--source", "winget",
                 "--count", "40", "--disable-interactivity"], runner)
    lines = raw.splitlines()
    head = next((i for i, line in enumerate(lines)
                 if re.search(r"\bId\b", line, re.I)
                 and re.search(r"\bVersion\b", line, re.I)), -1)
    packages = []
    if head >= 0:
        line = lines[head]
        id_match = re.search(r"\bId\b", line, re.I)
        version_match = re.search(r"\bVersion\b", line, re.I)
        left, right = id_match.start(), version_match.start()
        if 0 < left < right and right - left >= 6:
            known = set()
            for row in lines[head + 1:]:
                if not row.strip() or re.fullmatch(r"[-─\s]+", row):
                    continue
                if len(row) < right:
                    continue
                package_id = row[left:right].strip()
                title = row[:left].strip()
                version = row[right:].strip().split()
                try:
                    checked_id(package_id)
                except DiscoveryError:
                    continue
                if title and package_id not in known and version:
                    known.add(package_id)
                    packages.append({"name": title[:140], "id": package_id,
                                     "version_label": version[0][:64],
                                     "source": "winget"})
    return {"source": "winget", "query": term, "packages": packages[:40],
            "output": raw[:12000], "results_are_owner_approved": False}


def show(package_id, runner=subprocess.run):
    identity = checked_id(package_id)
    output = _call(["winget", "show", "--id", identity, "--exact", "--source",
                    "winget", "--disable-interactivity"], runner)
    if not output.strip():
        raise DiscoveryError("WinGet did not return package metadata")
    return {"package_id": identity, "source": "winget",
            "details": output[:12000], "hamapp_publisher_verified": False}


def installed_packages(*, runner=subprocess.run, reader=read_installed_inventory):
    """Read private machine-local WinGet inventory; never upload installed apps."""
    if not _on_windows():
        raise DiscoveryError("WinGet requires native Windows")
    try:
        rows = reader(runner=runner)
    except (StateError, ValueError, OSError) as exc:
        raise DiscoveryError("WinGet installed inventory unavailable or untrusted") from exc
    return {"source": "winget", "packages": rows,
            "results_are_owner_approved": False}


def execute_external(package_id, operation, *, runner=subprocess.run,
                     verifier=read_installed_version):
    """Invoke interactive official WinGet on a user-selected third-party ID.

    This is not a HamApp-published package or equivalent to the owner-approved
    catalog. Source is hard-pinned; OS dialogs and package EULAs stay visible.
    """
    identity = checked_id(package_id)
    if operation not in ("install", "upgrade", "uninstall"):
        raise DiscoveryError("only explicit third-party install/upgrade/uninstall is supported")
    # Reconfirm exact official source metadata before every state change.
    show(identity, runner=runner)
    if not _on_windows():
        raise DiscoveryError("WinGet requires native Windows")
    try:
        previous = verifier(identity)
    except (StateError, ValueError) as exc:
        raise DiscoveryError("installed package preflight is not trustworthy") from exc
    if operation in ("upgrade", "uninstall") and previous is None:
        raise DiscoveryError("cannot update/remove a package not confirmed installed")
    if operation == "install" and previous is not None:
        raise DiscoveryError("already installed; use explicit upgrade instead")
    cmd = ["winget", operation, "--id", identity, "--exact", "--source", "winget",
           "--interactive"]
    if operation == "install":
        cmd.append("--no-upgrade")
    try:
        result = runner(cmd, shell=False, timeout=3600, check=False,
                        creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0))
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DiscoveryError("interactive WinGet execution failed or timed out") from exc
    if result.returncode != 0:
        raise DiscoveryError("WinGet reported failure; installed state not accepted")
    try:
        after = verifier(identity)
    except (StateError, ValueError) as exc:
        raise DiscoveryError("WinGet ended but independent installed readback failed") from exc
    if operation == "uninstall":
        if after is not None:
            raise DiscoveryError("WinGet ended but package remains installed")
    else:
        if after is None:
            raise DiscoveryError("WinGet ended but matching package was not registered")
        if operation == "upgrade" and numeric_version(after) <= numeric_version(previous):
            raise DiscoveryError("WinGet ended without an independently confirmed newer version")
    # Do not claim an installer signature or an owner-approved publisher.
    return {"package_id": identity, "source": "winget", "operation": operation,
            "installed_version_readback": after,
            "removed_from_winget_inventory": operation == "uninstall",
            "hamapp_publisher_verified": False,
            "installer_signature_independently_verified": False}
