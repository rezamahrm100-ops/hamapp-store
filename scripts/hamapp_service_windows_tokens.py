"""Safe Windows owner-only Docker publisher token lifecycle UI.

No cmd.exe interpolation, shell, background mutation or other docker projects.
Token rotate/revoke changes ONLY the HamApp private registry. The backend
prints a newly minted token once; users must copy the new one to the client.
"""
import re
import subprocess
import sys
from hamapp_service_windows_setup import command_prefix, ProvisionError, PROJECT

ALLOWED = frozenset({"add", "rotate", "revoke"})
PUBLISHER = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")

def modify(action, publisher, *, runner=subprocess.run):
    if sys.platform != "win32":
        raise ProvisionError("Windows owner helper only")
    if action not in ALLOWED or not PUBLISHER.fullmatch(publisher):
        raise ProvisionError("invalid bounded token lifecycle operation")
    argv = command_prefix() + [
        "run", "--rm", "--no-deps", "-T", "publisher-intake",
        action, "--root", "/data/service", "--publisher", publisher]
    outcome = runner(argv, cwd=PROJECT, timeout=90, check=False)
    if outcome.returncode:
        raise ProvisionError("private service did not commit requested token operation")
    return True

def main():
    try:
        print("HamApp private publisher token administration")
        print("A new token is shown only once by the private backend; no release is approved.")
        action = input("Action (add/rotate/revoke): ").strip().lower()
        publisher = input("Publisher ID (lowercase/number/hyphen): ").strip()
        if action not in ALLOWED or not PUBLISHER.fullmatch(publisher):
            raise ProvisionError("invalid action or publisher ID")
        if input("Confirm only this publisher's private token operation? [yes/N]: ").strip().lower() != "yes":
            raise ProvisionError("operator declined")
        modify(action, publisher)
        print("PRIVATE_PUBLISHER_TOKEN_OPERATION=SUCCESS; NO_PUBLICATION")
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print("HAMAPP_PRIVATE_TOKEN_OPERATION_DENIED:", type(exc).__name__, file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
