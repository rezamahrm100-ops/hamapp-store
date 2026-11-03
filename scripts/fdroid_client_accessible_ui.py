#!/usr/bin/env python3
"""Select genuine current F-Droid emulator UI buttons by actual accessibility XML.

This helper NEVER has arbitrary coordinate defaults. It clicks only visible
clickable nodes in the official F-Droid package with exact relevant labels,
from an XML tree produced by the Android device under test. No owner devices.
"""
import argparse
import re
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

BOUNDS = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]\Z")
CONTROLS = {
    "add", "add repo", "add repository", "add new repository",
    "enable", "ok", "save", "confirm", "continue",
    "allow", "next", "done", "refresh", "sync", "update"
}
PACKAGE = "org.fdroid.fdroid"


def select(xml):
    root = ET.parse(xml).getroot()
    for parent in root.iter("node"):
        if parent.attrib.get("package") != PACKAGE:
            continue
        nodes = [parent] + list(parent.iter("node"))[:4]
        labels = [node.attrib.get("text", "").strip().lower()
                  for node in nodes]
        labels += [node.attrib.get("content-desc", "").strip().lower()
                   for node in nodes]
        if not any(value in CONTROLS for value in labels):
            continue
        target = parent
        if target.attrib.get("clickable") != "true":
            target = next((node for node in nodes
                           if node.attrib.get("clickable") == "true"
                           and node.attrib.get("package") == PACKAGE), None)
        if target is None:
            continue
        bounds = BOUNDS.fullmatch(target.attrib.get("bounds", ""))
        if not bounds:
            continue
        x1, y1, x2, y2 = map(int, bounds.groups())
        if x1 >= x2 or y1 >= y2 or x2 > 4096 or y2 > 4096:
            continue
        return (x1 + x2) // 2, (y1 + y2) // 2
    return None


def select_actual_repository_add(xml):
    """Select the actual F-Droid Add repository button using live UI hierarchy.

    Android accessibility commonly exposes the button label as a nonclickable
    TextView nested inside a clickable button container. A title with the same
    text must NOT trigger a tap. Choose only the smallest clickable F-Droid
    ancestor enclosing the exact label, with button-sized visible bounds.
    """
    root = ET.parse(xml).getroot()
    parent_of = {child: parent for parent in root.iter("node")
                 for child in parent.findall("node")}
    candidates = []
    for node in root.iter("node"):
        if node.attrib.get("package") != PACKAGE:
            continue
        label = (node.attrib.get("text", "") or
                 node.attrib.get("content-desc", "")).strip().casefold()
        if label != "add repository":
            continue
        current = node
        while current is not None and current.attrib.get("package") == PACKAGE:
            if current.attrib.get("clickable") == "true":
                match = BOUNDS.fullmatch(current.attrib.get("bounds", ""))
                if match:
                    x1, y1, x2, y2 = map(int, match.groups())
                    width, height = x2 - x1, y2 - y1
                    # Restrict to a visible small button, not the screen,
                    # toolbar or a large wrapping layout.
                    if (0 <= x1 < x2 <= 4096 and 0 <= y1 < y2 <= 4096
                            and 24 <= width <= 650 and 20 <= height <= 180):
                        candidates.append((width * height, (x1 + x2) // 2,
                                           (y1 + y2) // 2))
                break
            current = parent_of.get(current)
    if not candidates:
        return None
    candidates.sort()
    return candidates[0][1], candidates[0][2]


def select_onboarding_hint_dismissal(xml):
    """Dismiss actual official F-Droid onboarding tooltip using live XML only.

    The genuine post-enrollment Discover screen sometimes displays the Filter
    tutorial above every refresh control. A network GET alone cannot tell us
    whether the UI is blocked. Never guess its button coordinates or touch
    Android system permission dialogs.
    """
    root = ET.parse(xml).getroot()
    parents = {child: parent for parent in root.iter("node")
               for child in parent.findall("node")}
    candidates = []
    for node in root.iter("node"):
        if node.attrib.get("package") != PACKAGE:
            continue
        label = (node.attrib.get("text", "") or
                 node.attrib.get("content-desc", "")).strip().casefold()
        if label != "got it":
            continue
        current = node
        while current is not None and current.attrib.get("package") == PACKAGE:
            if current.attrib.get("clickable") == "true":
                bounds = BOUNDS.fullmatch(current.attrib.get("bounds", ""))
                if bounds:
                    x1, y1, x2, y2 = map(int, bounds.groups())
                    w, h = x2 - x1, y2 - y1
                    if (0 <= x1 < x2 <= 4096 and 0 <= y1 < y2 <= 4096
                            and 24 <= w <= 650 and 20 <= h <= 180):
                        candidates.append((w * h, (x1 + x2) // 2,
                                           (y1 + y2) // 2))
                break
            current = parents.get(current)
    if not candidates:
        return None
    candidates.sort()
    return candidates[0][1], candidates[0][2]


def select_unneeded_notification_denial(xml):
    """Dismiss ONLY the real Android notification prompt for official F-Droid.

    Never grant Android permissions, click an unrelated system permission
    dialog, or guess a coordinate. The observed prompt is system-owned, not
    an F-Droid view, and was blocking the official repo-add confirmation.
    """
    root = ET.parse(xml).getroot()
    nodes = [node for node in root.iter("node")
             if node.attrib.get("package") in (
                 "com.android.permissioncontroller",
                 "com.google.android.permissioncontroller")]
    visible_text = " ".join((node.attrib.get("text", "")
                             + " " + node.attrib.get("content-desc", ""))
                            for node in nodes).lower()
    if not ("notification" in visible_text
            and ("f-droid" in visible_text or "fdroid" in visible_text)):
        return None
    for node in nodes:
        label = (node.attrib.get("text", "") or
                 node.attrib.get("content-desc", "")).strip().lower()
        if label.replace("’", "'") not in ("don't allow", "deny"):
            continue
        target = node
        if target.attrib.get("clickable") != "true":
            target = next((parent for parent in nodes
                           if parent.attrib.get("clickable") == "true"
                           and node in list(parent.iter("node"))), None)
        if target is None:
            continue
        bounds = BOUNDS.fullmatch(target.attrib.get("bounds", ""))
        if not bounds:
            continue
        x1, y1, x2, y2 = map(int, bounds.groups())
        if x1 >= x2 or y1 >= y2 or x2 > 4096 or y2 > 4096:
            continue
        return (x1 + x2) // 2, (y1 + y2) // 2
    return None


def main():
    p = argparse.ArgumentParser(description="Real official-client accessible UI selection only")
    p.add_argument("--xml", type=Path, required=True)
    p.add_argument("--deny-notification-prompt", action="store_true")
    p.add_argument("--dismiss-onboarding", action="store_true")
    p.add_argument("--confirm-repository-add", action="store_true")
    a = p.parse_args()
    try:
        if sum((a.deny_notification_prompt, a.confirm_repository_add,
                a.dismiss_onboarding)) > 1:
            raise ValueError("only one restricted UI selector is allowed")
        action = (select_unneeded_notification_denial(a.xml)
                  if a.deny_notification_prompt else
                  select_onboarding_hint_dismissal(a.xml)
                  if a.dismiss_onboarding else
                  select_actual_repository_add(a.xml)
                  if a.confirm_repository_add else select(a.xml))
    except (OSError, ET.ParseError, ValueError):
        return 2
    if action is None:
        return 1
    print(action[0], action[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
