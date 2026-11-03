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
    a = p.parse_args()
    try:
        action = (select_unneeded_notification_denial(a.xml)
                  if a.deny_notification_prompt else select(a.xml))
    except (OSError, ET.ParseError, ValueError):
        return 2
    if action is None:
        return 1
    print(action[0], action[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
