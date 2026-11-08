#!/usr/bin/env python3
"""Check real emulator accessibility hierarchy; reject missing/active install UI."""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


def check_ui(path, scrolled=None):
    # The top-level title is fixed. The owner-reviewed app cards reside in a
    # separate ScrollView: the capture after a native swipe is necessary on
    # small Android displays. Both snapshots must be from the same foreground
    # package, and failure to capture either never passes acceptance.
    root = ET.parse(path).getroot()
    top_nodes = list(root.iter("node"))
    if not any(n.attrib.get("text", "") == "هَماپ" for n in top_nodes):
        raise ValueError("HamApp title not rendered on emulator")
    if scrolled is not None:
        second = ET.parse(scrolled).getroot()
        bottom_nodes = list(second.iter("node"))
    else:
        bottom_nodes = []
    nodes = top_nodes + bottom_nodes
    labels = [n.attrib.get("text", "") for n in nodes]
    if not any(label == "هَماپ" for label in labels):
        raise ValueError("HamApp title not rendered on emulator")
    # Distinguish approved-repository install handoff (must be disabled when
    # no owner-approved release) from public F-Droid app launch (must work).
    fdroid = [n for n in nodes if n.attrib.get("text", "") == "مدیریت در هَماپ"]
    public = [n for n in nodes if n.attrib.get("text", "") == "برنامه‌های عمومی"]
    if not fdroid:
        raise ValueError("HamApp owner install button not rendered")
    if any(n.attrib.get("enabled") != "false" for n in fdroid):
        raise ValueError("unverified owner install must be disabled")
    if len(public) != 1 or public[0].attrib.get("enabled") != "true":
        raise ValueError("embedded public F-Droid storefront must be enabled")
    if not any("در دست توسعه" in label for label in labels):
        raise ValueError("planned app status not rendered")
    return len(fdroid)


def main():
    if len(sys.argv) not in (2, 3):
        raise SystemExit("usage: check_android_emulator_ui.py TOP_XML [SCROLLED_XML]")
    n = check_ui(Path(sys.argv[1]), Path(sys.argv[2]) if len(sys.argv) == 3 else None)
    print(f"ANDROID_EMULATOR_UI_PASS: {n} F-Droid action(s) disabled")


if __name__ == "__main__":
    main()
