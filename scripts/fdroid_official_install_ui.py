#!/usr/bin/env python3
"""Bounded actual accessibility controls for disposable official F-Droid install QA.

No static coordinates, no owner device, no bypass of Android package installer.
This selector NEVER establishes installation: independent package-manager and
on-device APK read-back is required for successful acceptance.
"""
import argparse
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

FDROID = "org.fdroid.fdroid"
INSTALLER_PACKAGES = frozenset({
    "com.google.android.packageinstaller", "com.android.packageinstaller",
    "com.google.android.permissioncontroller", "com.android.permissioncontroller",
})
APP_LABELS = frozenset(("هَماپ", "هماپ", "HamApp"))
BOUNDS = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]\Z")


def _text(node):
    return (node.get("text", "") or node.get("content-desc", "")).strip()


def _point(node):
    bounds = BOUNDS.fullmatch(node.get("bounds", ""))
    if bounds is None:
        return None
    x1, y1, x2, y2 = map(int, bounds.groups())
    if not (0 <= x1 < x2 <= 4096 and 0 <= y1 < y2 <= 4096):
        return None
    if not (24 <= x2 - x1 <= 650 and 20 <= y2 - y1 <= 180):
        return None
    return (x1 + x2) // 2, (y1 + y2) // 2



def source_settings_state(xml_file):
    """Inspect ONLY a real F-Droid-scoped Android Settings permission screen.

    Return true/false for a unique actual visible system switch. Never
    infer permission from sending a tap, a screenshot or a shell appop.
    """
    root = ET.parse(xml_file).getroot()
    nodes = [node for node in root.iter("node")
             if node.get("package") == "com.android.settings"]
    labels = { _text(node).casefold() for node in nodes if _text(node) }
    if not ({"f-droid", "install unknown apps", "allow from this source"} <= labels):
        return None
    switches = [node for node in nodes
                if "switch" in node.get("class", "").casefold()
                and node.get("checked") in ("true", "false")
                and node.get("enabled") == "true"
                and _point(node) is not None]
    if len(switches) != 1:
        return None
    return switches[0].get("checked") == "true"



def select(xml_file, action):
    if action not in ("install", "update", "dismiss-hint", "confirm-installer",
                      "confirm-metered", "open-source-settings", "allow-source-settings"):
        raise ValueError("restricted action required")
    root = ET.parse(xml_file).getroot()
    nodes = list(root.iter("node"))
    parents = {node: parent for parent in nodes for node in parent.findall("node")}
    if action == "open-source-settings":
        allowed = INSTALLER_PACKAGES
    elif action == "allow-source-settings":
        allowed = frozenset(("com.android.settings",))
        if source_settings_state(xml_file) is not False:
            return None
    else:
        allowed = INSTALLER_PACKAGES if action == "confirm-installer" else frozenset((FDROID,))
    scoped = [node for node in nodes if node.get("package") in allowed]
    if action == "open-source-settings":
        visible = " ".join(_text(node) for node in scoped).casefold()
        if "f-droid" not in visible or "unknown apps from this source" not in visible:
            return None
    elif action == "allow-source-settings":
        pass  # exact settings page and unique unchecked switch above
    elif action == "confirm-metered":
        # Official F-Droid upstream MeteredConnectionDialog: only proceed
        # when the real application-owned prompt title and button coexist.
        # The only network here is the disposable isolated test repository;
        # this does not grant unknown-source installation permissions.
        if not any(_text(node).casefold() == "continue with mobile data?"
                   for node in scoped):
            return None
    elif action != "dismiss-hint" and not any(
            _text(node) in APP_LABELS or "ir.hamapp.store" in _text(node)
            for node in scoped):
        return None
    desired = {
        "install": ("install",),
        "update": ("update",),
        "dismiss-hint": ("got it",),
        "confirm-installer": ("install", "update"),
        "confirm-metered": ("download",),
        "open-source-settings": ("settings",),
        "allow-source-settings": (),
    }[action]
    candidates = []
    for node in scoped:
        if action == "allow-source-settings":
            if not ("switch" in node.get("class", "").casefold()
                    and node.get("checked") == "false"
                    and node.get("enabled") == "true"):
                continue
        elif _text(node).casefold() not in desired:
            continue
        current = node
        while current is not None and current.get("package") in allowed:
            if current.get("clickable") == "true":
                p = _point(current)
                if p:
                    match = BOUNDS.fullmatch(current.get("bounds", ""))
                    x1, y1, x2, y2 = map(int, match.groups())
                    candidates.append(((x2 - x1) * (y2 - y1), p))
                break
            current = parents.get(current)
    if not candidates:
        return None
    candidates.sort()
    return candidates[0][1]


def main():
    parser = argparse.ArgumentParser(description="Official client actual bounded UI control")
    parser.add_argument("--xml", type=Path, required=True)
    parser.add_argument("--action", choices=("install", "update", "dismiss-hint",
                                           "confirm-installer", "confirm-metered",
                                           "open-source-settings", "allow-source-settings"), required=True)
    args = parser.parse_args()
    try:
        point = select(args.xml, args.action)
    except (OSError, ET.ParseError, ValueError):
        return 2
    if point is None:
        return 1
    print(*point)
    return 0


if __name__ == "__main__":
    sys.exit(main())
