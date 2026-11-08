"""Windows-side one-command Docker Desktop service provisioning.

Only the exact private HamApp publisher service is built or started. Never
stops, prunes, modifies or configures unrelated Docker services and never puts
private signing keys on command line, in the repository or in build logs.
"""
import hashlib
from pathlib import Path
import re
import secrets
import shutil
import ssl
import struct
import os
import time
import subprocess
import sys

PROJECT = Path(__file__).resolve().parents[1]
COMPOSE = PROJECT / "deployment/compose.yaml"
PUBLISHER = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
MAX_PEM = 256000

class ProvisionError(ValueError):
    pass

def envelope(public, private):
    cert, key = Path(public), Path(private)
    if (cert.is_symlink() or key.is_symlink() or
            not cert.is_file() or not key.is_file()):
        raise ProvisionError("certificate/key must be existing non-symlink files")
    if cert.resolve() == key.resolve() or cert.stat().st_size > MAX_PEM or key.stat().st_size > MAX_PEM:
        raise ProvisionError("TLS certificate/key missing or oversized")
    left, right = cert.read_bytes(), key.read_bytes()
    if (not left.startswith(b"-----BEGIN CERTIFICATE-----") or
            b"-----BEGIN " not in right or b"PRIVATE KEY-----" not in right):
        raise ProvisionError("expected PEM certificate and private key")
    return struct.pack("!II", len(left), len(right)) + left + right

def command_prefix():
    if not COMPOSE.is_file():
        raise ProvisionError("service packaging is incomplete: compose.yaml missing")
    if shutil.which("docker") is None:
        raise ProvisionError("Docker Desktop/Engine is unavailable; install it before enabling the private service")
    return ["docker", "compose", "-f", str(COMPOSE), "-p", "hamapp-private"]

def init(publisher, cert=None, key=None, *, runner=subprocess.run):
    if sys.platform != "win32":
        raise ProvisionError("one-click launcher is for Windows; POSIX can use hamapp_operator.py directly")
    if not isinstance(publisher, str) or not PUBLISHER.fullmatch(publisher):
        raise ProvisionError("publisher must use lowercase letters, digits and hyphens")
    if (cert is None) != (key is None):
        raise ProvisionError("a custom certificate requires its matching private key")
    packet = envelope(cert, key) if cert is not None else None
    # The caller owns the high-entropy secret; Docker never prints or logs it.
    token = secrets.token_urlsafe(48)
    prefix = command_prefix()
    build = runner(prefix + ["build", "publisher-intake"],
                   cwd=PROJECT, timeout=900, capture_output=True, check=False)
    if build.returncode:
        raise ProvisionError("private Docker service could not be built; inspect Docker Desktop")
    args = prefix + ["run", "--rm", "--no-deps", "-T", "publisher-intake",
                     "init", "--root", "/data/service", "--publisher", publisher]
    args.append("--dev-local-cert" if packet is None else "--import-stdin")
    args.append("--token-stdin")
    applied = runner(args, input=(packet or b"") + token.encode("ascii"),
                     cwd=PROJECT, timeout=120,
                     capture_output=True, check=False)
    if applied.returncode:
        # Private backend rejects re-initializing a preexisting identity and
        # never overwrites its previous credential registry/cert/key.
        raise ProvisionError("private service refused initialization; existing data was not overwritten")
    started = runner(prefix + ["up", "-d", "--no-build", "publisher-intake"],
                     cwd=PROJECT, timeout=120, capture_output=True, check=False)
    if started.returncode:
        raise ProvisionError("service identity provisioned; Docker service did not start")
    lines = applied.stdout.decode("utf-8", errors="replace").splitlines()
    # Reject accidental reintroduction of credential logging by the backend.
    if any("ONE_TIME_PUBLISHER_TOKEN" in line or token in line for line in lines):
        raise ProvisionError("private backend emitted forbidden secret material")
    pin = next((line.removeprefix("TLS_LEAF_SHA256: ").strip()
                for line in lines if line.startswith("TLS_LEAF_SHA256: ")), None)
    if not pin or not re.fullmatch("[a-f0-9]{64}", pin):
        raise ProvisionError("service setup returned no valid private identity receipt")
    exported = runner(prefix + [
        "run", "--rm", "--no-deps", "-T", "publisher-intake",
        "export-ca", "--root", "/data/service"
    ], cwd=PROJECT, timeout=75, capture_output=True, check=False)
    if exported.returncode or not exported.stdout.startswith(b"-----BEGIN CERTIFICATE-----"):
        raise ProvisionError("service public TLS certificate export failed")
    if hashlib.sha256(ssl.PEM_cert_to_DER_cert(
            exported.stdout.decode("ascii"))).hexdigest() != pin:
        raise ProvisionError("public certificate digest does not match service pin")
    # The PUBLIC certificate is safe to copy to the user's local application
    # settings. The private key never leaves the isolated container volume.
    from windows_client import publisher_connection as connection
    local = Path(os.environ.get("LOCALAPPDATA") or "")
    if not local.is_dir():
        raise ProvisionError("Windows LOCALAPPDATA unavailable")
    target = local / "HamAppStore" / "private-intake-localhost-ca.pem"
    if target.is_symlink():
        raise ProvisionError("unsafe public certificate destination")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(exported.stdout)
    details = {"publisher": publisher, "origin": "https://localhost:8766",
               "trusted_ca": str(target), "server_cert_sha256": pin}
    connection.save_profile(details, token)
    # The service may require several seconds for its TLS listener to boot.
    ready = False
    for _ in range(4):
        try:
            proof = connection.probe(details)
            ready = proof["tls_pinned"] and proof["quarantine_api_reachable"]
            if ready:
                break
        except (OSError, ValueError, ssl.SSLError):
            pass
        time.sleep(1)
    return {"publisher": publisher, "tls_sha256": pin,
            "origin": details["origin"], "trusted_ca_pem": str(target),
            "service_started": ready, "secure_windows_profile_saved": True,
            "public_release_authorized": False}

def main():
    if sys.platform != "win32":
        raise SystemExit("Run this launcher on Windows 11 with Docker Desktop enabled.")
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        print("HamApp private publisher service — local-only Docker listener")
        publisher = input("Publisher repository ID (lowercase-hyphens): ").strip()
        use_existing = input("Bring your own TLS certificate/key? [y/N]: ").strip().lower() == "y"
        public = private = None
        if use_existing:
            public = filedialog.askopenfilename(title="Choose trusted TLS public certificate PEM",
                                                filetypes=[("PEM", "*.pem *.crt"), ("All files", "*.*")])
            private = filedialog.askopenfilename(title="Choose existing TLS private key PEM",
                                                 filetypes=[("PEM key", "*.pem *.key"), ("All files", "*.*")])
            if not public or not private:
                raise ProvisionError("operator cancelled certificate/key selection")
        root.destroy()
        result = init(publisher, public, private)
        print("HAMAPP_LOCAL_QUARANTINE_SERVICE_REACHABLE=" +
              ("YES" if result["service_started"] else "NOT_VERIFIED"))
        print("HAMAPP_WINDOWS_ACCOUNT_CONFIGURED_WITH_DPAPI=YES")
        print("PUBLISHER:", result["publisher"])
        print("TLS_SERVER_LEAF_SHA256:", result["tls_sha256"])
        print("SERVER_ORIGIN:", result["origin"])
        print("PUBLIC_CA_FILE:", result["trusted_ca_pem"])
        print("Publisher token generated locally and stored in the Windows DPAPI profile, not logged.")
        print("Not a production publisher approval or public release.")
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print("HAMAPP_LOCAL_SERVICE_SETUP_FAILED:", type(exc).__name__, file=sys.stderr)
        raise SystemExit(1)

if __name__ == "__main__":
    main()
