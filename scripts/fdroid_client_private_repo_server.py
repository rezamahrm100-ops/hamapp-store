#!/usr/bin/env python3
"""Serve ONLY signed public F-Droid test repo files to Android 10.0.2.2.

Never serves fdroid config, generated keystore, password or private signer. The
live request log is a temporary test-only file outside the public webroot.
"""
from functools import partial
import http.server
import json
import os
from pathlib import Path
import re
import ssl

PORT = 8975


class ProbeHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # Never log source config, tokens or query strings. Record only public
        # expected signed repo paths and user agent to distinguish Android app
        # HTTP requests from synthetic host curl.
        path = self.path.split("?", 1)[0]
        if not re.fullmatch(r"/fdroid/repo/[A-Za-z0-9._+/-]{1,160}", path):
            return
        event = {
            "method": self.command,
            "path": path,
            "agent": self.headers.get("User-Agent", "")[:160],
        }
        filename = Path(os.environ["RUNNER_TEMP"]) / "hamapp-fdroid-real-official-client-lab/requests.jsonl"
        with filename.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, sort_keys=True) + "\n")


def main():
    if os.environ.get("GITHUB_ACTIONS") != "true" or os.environ.get("RUNNER_OS") != "Linux":
        raise SystemExit("HOSTED_CI_ONLY")
    public = Path(os.environ["RUNNER_TEMP"]) / "hamapp-fdroid-real-official-client-lab/webroot"
    if public.is_symlink() or not (public / "fdroid/repo/entry.jar").is_file():
        raise SystemExit("REAL_SIGNED_REPO_REQUIRED")
    server = http.server.ThreadingHTTPServer(
        ("127.0.0.1", PORT), partial(ProbeHandler, directory=str(public)))
    server.daemon_threads = True
    # The currently GPG/authenticode-pinned official F-Droid client only
    # registers fdroidrepos (HTTPS), not the legacy fdroidrepo HTTP intent.
    # Serve a true TLS endpoint using a throwaway local private CA whose
    # public certificate is trusted ONLY in this isolated emulator.
    certs = Path(os.environ["RUNNER_TEMP"]) / "hamapp-fdroid-real-official-client-lab/tls"
    cert, key = certs / "server.pem", certs / "server.key"
    if (cert.is_symlink() or key.is_symlink() or not cert.is_file()
            or not key.is_file() or key.stat().st_mode & 0o077):
        raise SystemExit("PRIVATE_TEMPORARY_TLS_SIGNER_MISSING_OR_UNSAFE")
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(str(cert), str(key))
    server.socket = context.wrap_socket(server.socket, server_side=True)
    print("ISOLATED_SIGNED_REPO_HTTPS_EMULATOR_ONLY_NOT_PUBLIC", flush=True)
    server.serve_forever(poll_interval=0.2)


if __name__ == "__main__":
    main()
