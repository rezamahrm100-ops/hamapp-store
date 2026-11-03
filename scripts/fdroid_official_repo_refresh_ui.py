#!/usr/bin/env python3
"""Real F-Droid repository details navigation and forced-update UI on hosted emulator.

The initial signed v2 index GET from a *repository-add preview* is NOT proof
F-Droid processed the installed repository's update. This script only taps
live, context-bound accessibility controls in the official application.
No ADB database writes, intent to an unexported worker, APK install or
permission grants. Exact index fetch and actual PM v2 readback happen outside.
"""
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET

FDROID = "org.fdroid.fdroid"
REPO_TITLE = "Disposable HamApp emulator install test only"
BOUNDS = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]\Z")


def _label(node):
    return (node.get("text", "") or node.get("content-desc", "")).strip()


def _point(node):
    match = BOUNDS.fullmatch(node.get("bounds", ""))
    if not match:
        return None
    x1, y1, x2, y2 = map(int, match.groups())
    w, h = x2 - x1, y2 - y1
    if not (0 <= x1 < x2 <= 4096 and 0 <= y1 < y2 <= 4096 and
            24 <= w <= 650 and 20 <= h <= 180):
        return None
    return (x1 + x2) // 2, (y1 + y2) // 2, w * h


def _ancestor_button(node, parents):
    current = node
    while current is not None and current.get("package") == FDROID:
        if current.get("clickable") == "true":
            result = _point(current)
            return result
        current = parents.get(current)
    return None


def select(xml_path, action):
    """Return live target only if correct upstream screen and exact button exist."""
    if action not in ("repositories", "test-repository", "force-update",
                      "dismiss-repo-hint", "back-from-app"):
        raise ValueError("unknown real F-Droid navigation action")
    root = ET.parse(xml_path).getroot()
    nodes = [n for n in root.iter("node") if n.get("package") == FDROID]
    parents = {child: parent for parent in root.iter("node")
               for child in parent.findall("node")}
    labels = {_label(n).casefold() for n in nodes if _label(n)}
    if action == "repositories":
        if "f-droid" not in labels or "repositories" not in labels:
            return None
        names = {"repositories"}
    elif action == "test-repository":
        if "repositories" not in labels or REPO_TITLE.casefold() not in labels:
            return None
        names = {REPO_TITLE.casefold()}
    elif action == "force-update":
        if REPO_TITLE.casefold() not in labels or "check for updates" not in labels:
            return None
        names = {"check for updates"}
    elif action == "dismiss-repo-hint":
        if ("repositories" not in labels and REPO_TITLE.casefold() not in labels):
            return None
        names = {"got it"}
    else:
        if not ({"hamapp", "هَماپ", "هماپ"} & labels):
            return None
        names = {"back"}
    choices = []
    for node in nodes:
        if _label(node).casefold() not in names:
            continue
        target = _ancestor_button(node, parents)
        if target is not None:
            x, y, size = target
            choices.append((size, x, y))
    if not choices:
        return None
    choices.sort()
    if action in ("test-repository", "force-update") and len(choices) > 1:
        # No ambiguous installed repository identity or refresh control.
        return None
    return choices[0][1], choices[0][2]


def adb(*args, timeout=25):
    process = subprocess.run(["adb", *args], check=False, capture_output=True,
                             text=True, timeout=timeout, errors="replace")
    if process.returncode:
        raise RuntimeError("hosted Android accessibility action failed")
    return process.stdout


def dump(dest):
    adb("shell", "uiautomator", "dump",
        "/sdcard/hamapp-fdroid-refresh-live.xml", timeout=30)
    adb("pull", "/sdcard/hamapp-fdroid-refresh-live.xml", str(dest), timeout=30)
    return dest


def run():
    if (os.environ.get("GITHUB_ACTIONS") != "true"
            or os.environ.get("RUNNER_OS") != "Linux"
            or os.environ.get("GITHUB_REPOSITORY") != "rezamahrm100-ops/hamapp-store"):
        raise RuntimeError("isolated GitHub-hosted Linux test only")
    # Only the official public launcher; this is not an internal worker intent.
    adb("shell", "am", "start", "-W", "-a", "android.intent.action.MAIN",
        "-c", "android.intent.category.LAUNCHER", "-p", FDROID, timeout=35)
    with tempfile.TemporaryDirectory(prefix="hamapp-official-ui-refresh-") as tmp:
        xml = Path(tmp) / "live.xml"
        transitions = []
        for attempt in range(24):
            try:
                dump(xml)
            except (OSError, subprocess.TimeoutExpired, RuntimeError):
                time.sleep(2)
                continue
            # Prefer force-update on actual repository details. No network GET
            # or old repository preview itself authorizes claiming completion.
            actions = ("force-update", "dismiss-repo-hint", "test-repository",
                       "repositories", "back-from-app")
            action, point = next(
                ((a, p) for a in actions if (p := select(xml, a)) is not None),
                (None, None))
            if action is None:
                time.sleep(2)
                continue
            adb("shell", "input", "tap", str(point[0]), str(point[1]))
            transitions.append(action)
            if action == "force-update":
                if ("repositories" not in transitions or
                        "test-repository" not in transitions):
                    raise RuntimeError("repository update did not follow genuine navigation")
                print("REAL_OFFICIAL_FDROID_REPO_DETAIL_FORCE_UPDATE_BUTTON_TAPPED")
                return
            time.sleep(2)
    raise RuntimeError("REAL_OFFICIAL_FDROID_REPO_FORCE_UPDATE_UI_NOT_REACHED")


if __name__ == "__main__":
    try:
        run()
    except (RuntimeError, OSError, ValueError, ET.ParseError, subprocess.TimeoutExpired) as e:
        print("REAL_OFFICIAL_FDROID_REPO_REFRESH_NOT_ACCEPTED: " + str(e),
              file=sys.stderr)
        sys.exit(1)
