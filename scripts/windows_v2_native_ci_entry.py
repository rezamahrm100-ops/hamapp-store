#!/usr/bin/env python3
"""Create test-only v2 Windows GUI native entrypoint for a REAL PyInstaller EXE.

No public release, no owner device, no trusted signature, no build action.
The source marker is visibly different in the actual GUI Window title.
"""
import argparse
import os
from pathlib import Path

ENTRY = '''"""Throwaway Windows CI native GUI v2 test entrypoint (not for release)."""
from windows_client.gui import main

if __name__ == "__main__":
    main(build_label="ci-test-v2")
'''


def write_entry(path):
    if os.name != "nt" or os.environ.get("GITHUB_ACTIONS") != "true" or os.environ.get("RUNNER_OS") != "Windows":
        raise ValueError("isolated hosted Windows CI only")
    root = Path(os.environ.get("RUNNER_TEMP", "")).resolve(strict=True)
    target = Path(path)
    if target.is_symlink() or target.exists() or target.suffix != ".py" or target.resolve().parent != root:
        raise ValueError("fresh temporary-only source entry path required")
    with target.open("x", encoding="utf-8") as stream:
        stream.write(ENTRY)
    if "ci-test-v2" not in target.read_text("utf-8"):
        raise ValueError("test-only v2 GUI source marker failed immutable readback")
    print("GITHUB_HOSTED_WINDOWS_REAL_V2_NATIVE_SOURCE_PREPARED_NOT_PRODUCTION")


def main():
    p = argparse.ArgumentParser(description="Temp-only actual second Windows GUI build")
    p.add_argument("--entry", type=Path, required=True)
    args = p.parse_args()
    try:
        write_entry(args.entry)
    except (ValueError, OSError, TypeError) as exc:
        p.exit(1, "PRIVATE_HOSTED_WINDOWS_V2_ENTRY_REJECTED: " + str(exc) + "\n")


if __name__ == "__main__":
    main()
