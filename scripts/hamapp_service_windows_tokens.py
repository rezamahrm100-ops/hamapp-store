"""Safe Windows owner-only Docker publisher token lifecycle UI.

No cmd.exe interpolation, shell, background mutation or other docker projects.
Token rotate/revoke changes ONLY the HamApp private registry. The backend
prints a newly minted token once; users must copy the new one to the client.
"""
import re
import secrets
import subprocess
import sys
from hamapp_service_windows_setup import command_prefix, ProvisionError, PROJECT
from windows_client import publisher_connection as connection

ALLOWED = frozenset({"add", "rotate", "revoke"})
PUBLISHER = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")

def modify(action, publisher, *, runner=subprocess.run):
    if sys.platform != "win32":
        raise ProvisionError("Windows owner helper only")
    if action not in ALLOWED or not PUBLISHER.fullmatch(publisher):
        raise ProvisionError("invalid bounded token lifecycle operation")
    token = secrets.token_urlsafe(48) if action in {"add", "rotate"} else None
    argv = command_prefix() + [
        "run", "--rm", "--no-deps", "-T", "publisher-intake",
        action, "--root", "/data/service", "--publisher", publisher]
    if token:
        argv.append("--token-stdin")
    outcome = runner(argv, input=(token.encode("ascii") if token else None),
                     cwd=PROJECT, timeout=90, capture_output=True, check=False)
    if outcome.returncode or (token and token in outcome.stdout.decode("utf-8", errors="replace")):
        raise ProvisionError("private service rejected operation or disclosed a credential")
    # Rotating the locally connected publisher updates its existing DPAPI
    # profile automatically, rather than leaving a stale secret in the GUI.
    try:
        existing = connection.read_profile()
        if existing and existing["details"]["publisher"] == publisher:
            if action == "revoke":
                connection.remove_profile()
            else:
                connection.save_profile(existing["details"], token)
    except (OSError, ValueError):
        raise ProvisionError("private registry changed but local DPAPI profile needs repair")
    return token

def main():
    try:
        print("HamApp private publisher token administration")
        print("Tokens are not printed to backend logs; new secrets can be copied from local Windows UI.")
        action = input("Action (add/rotate/revoke): ").strip().lower()
        publisher = input("Publisher ID (lowercase/number/hyphen): ").strip()
        if action not in ALLOWED or not PUBLISHER.fullmatch(publisher):
            raise ProvisionError("invalid action or publisher ID")
        if input("Confirm only this publisher's private token operation? [yes/N]: ").strip().lower() != "yes":
            raise ProvisionError("operator declined")
        token = modify(action, publisher)
        print("PRIVATE_PUBLISHER_TOKEN_OPERATION=SUCCESS; NO_PUBLICATION")
        if token:
            # User-local selectable GUI; no console/log/stdout disclosure.
            import tkinter as tk
            dialog = tk.Tk()
            dialog.title("HamApp private token — copy once")
            dialog.geometry("570x140")
            tk.Label(dialog, text="Private token: copy it to the intended account, then close this window.").pack(pady=8)
            field = tk.Entry(dialog, width=76)
            field.insert(0, token)
            field.configure(state="readonly")
            field.pack(pady=6)
            def copy_token():
                dialog.clipboard_clear()
                dialog.clipboard_append(token)
            tk.Button(dialog, text="Copy token", command=copy_token).pack(pady=6)
            dialog.mainloop()
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print("HAMAPP_PRIVATE_TOKEN_OPERATION_DENIED:", type(exc).__name__, file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
