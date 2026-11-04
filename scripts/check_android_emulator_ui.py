#!/usr/bin/env python3
"""Check real emulator accessibility hierarchy; reject missing/active install UI."""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


def check_ui(path):
    root = ET.parse(path).getroot()
    nodes = list(root.iter("node"))
    labels = [n.attrib.get("text", "") for n in nodes]
    if not any("هَماپ" in label for label in labels):
        raise ValueError("HamApp title not rendered on emulator")
    # Distinguish approved-repository install handoff (must be disabled when
    # no owner-approved release) from public F-Droid app launch (must work).
    fdroid = [n for n in nodes if n.attrib.get("text", "") == "مدیریت از طریق F-Droid"]
    public = [n for n in nodes if n.attrib.get("text", "") == "بازکردن فروشگاه عمومی F-Droid"]
    if not fdroid:
        raise ValueError("F-Droid handoff button not rendered")
    if any(n.attrib.get("enabled") != "false" for n in fdroid):
        raise ValueError("unverified F-Droid handoff must be disabled")
    if len(public) != 1 or public[0].attrib.get("enabled") != "true":
        raise ValueError("separate public F-Droid launcher must be enabled")
    if not any("در دست توسعه" in label for label in labels):
        raise ValueError("planned app status not rendered")
    return len(fdroid)


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: check_android_emulator_ui.py WINDOW_XML")
    n = check_ui(Path(sys.argv[1]))
    print(f"ANDROID_EMULATOR_UI_PASS: {n} F-Droid action(s) disabled")


if __name__ == "__main__":
    main()
