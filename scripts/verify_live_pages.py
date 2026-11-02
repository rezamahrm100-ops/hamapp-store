#!/usr/bin/env python3
"""Verify ACTUAL deployed GitHub Pages HTTPS bytes against local built site.

No redirects, plain HTTP, alternative domains, insecure TLS, cached assertions
or secret inputs. Real main Pages deploy runs this after the official Pages
action; this checks currently delivered public static bytes, not publisher
application origin authenticity, cryptographic build provenance or uptime.
"""
import argparse
import hashlib
import json
from pathlib import Path
import ssl
import time
import urllib.error
import urllib.request

ORIGIN = "https://rezamahrm100-ops.github.io/hamapp-store/"
FILES = (
    "index.html", "app.js", "sw.js", "styles.css", "manifest.webmanifest",
    "catalog/apps.json", "catalog/planned-offline.json",
)
MAX_BYTES = 5 * 1024 * 1024

class LivePagesError(ValueError):
    pass

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise LivePagesError("public deployment unexpectedly redirected")

def check_site(site_dir, *, origin=ORIGIN, opener=None):
    if origin != ORIGIN:
        raise LivePagesError("exact reviewed production Pages HTTPS origin required")
    root = Path(site_dir)
    if root.is_symlink() or not root.is_dir():
        raise LivePagesError("invalid trusted local build directory")
    if opener is None:
        opener = urllib.request.build_opener(
            NoRedirect(), urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    records = []
    for path in FILES:
        local = root / path
        if local.is_symlink() or not local.is_file():
            raise LivePagesError("required site file missing or symlink: " + path)
        local_bytes = local.read_bytes()
        if not 0 < len(local_bytes) <= MAX_BYTES:
            raise LivePagesError("invalid local site file size: " + path)
        url = origin + path
        request = urllib.request.Request(
            url, headers={"User-Agent": "HamApp-TrustedMain-Pages-QA/1.0",
                          "Cache-Control": "no-cache", "Pragma": "no-cache"})
        try:
            with opener.open(request, timeout=25) as response:
                status = response.getcode()
                final_url = response.geturl()
                deployed = response.read(MAX_BYTES + 1)
        except LivePagesError:
            raise
        except (urllib.error.HTTPError, urllib.error.URLError,
                TimeoutError, OSError) as exc:
            raise LivePagesError("public HTTPS deployment unavailable: " + path) from exc
        if status != 200 or final_url != url:
            raise LivePagesError("unexpected HTTP status or redirect: " + path)
        if len(deployed) != len(local_bytes) or deployed != local_bytes:
            raise LivePagesError("deployed bytes do not match exact built site: " + path)
        records.append({"path": path, "sha256": hashlib.sha256(local_bytes).hexdigest(),
                        "size_bytes": len(local_bytes)})
    return {
        "schema_version": 1, "public_origin": ORIGIN,
        "expected_public_files_checked": len(records), "files": records,
        "actual_https_bytes_match_local_build": True,
        "redirects_disallowed": True, "default_CA_and_hostname_verification": True,
        "target_app_binary_approval_verified": False,
        "publisher_web_app_origin_approved": False,
        "source_build_attestation_independently_verified": False,
        "public_release_authorized": False,
    }

def main():
    p = argparse.ArgumentParser(description="Actual HTTPS site byte parity after Pages deploy")
    p.add_argument("--site-dir", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    p.add_argument("--attempts", type=int, default=12)
    p.add_argument("--retry-seconds", type=int, default=5)
    args = p.parse_args()
    if not 1 <= args.attempts <= 20 or not 0 <= args.retry_seconds <= 30:
        p.exit(1, "INVALID_DEPLOYMENT_RETRY_POLICY\n")
    try:
        if args.receipt.exists() or args.receipt.is_symlink():
            raise LivePagesError("receipt already exists")
        receipt = None
        for i in range(args.attempts):
            try:
                receipt = check_site(args.site_dir)
                break
            except LivePagesError:
                if i == args.attempts - 1:
                    raise
                time.sleep(args.retry_seconds)
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        with args.receipt.open("x", encoding="utf-8") as out:
            json.dump(receipt, out, ensure_ascii=False, indent=2, sort_keys=True)
            out.write("\n")
    except (OSError, LivePagesError, UnicodeError) as exc:
        p.exit(1, "LIVE_PAGES_REJECTED: " + str(exc) + "\n")
    print("ACTUAL_DEPLOYED_HTTPS_BYTES_MATCH_BUILT_SOURCE; APP_PUBLISHER_RELEASE_NOT_APPROVED")

if __name__ == "__main__":
    main()
