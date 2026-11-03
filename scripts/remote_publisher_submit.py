#!/usr/bin/env python3
"""Pinned-CA AND exact TLS server certificate SHA256 publisher uploader.

A publisher token is never sent until Python OpenSSL has independently
validated the HTTPS chain, hostname and an out-of-band known server leaf pin.
The receiving API ONLY quarantines the actual binary, never approves it.
"""
import argparse
import hashlib
import hmac
import http.client
import json
from pathlib import Path
import re
import ssl
from urllib.parse import urlsplit

import local_publisher_submit as local
import publisher_intake_service as local_gateway

SHA = re.compile(r"[0-9a-f]{64}\Z")


class RemotePublisherError(ValueError):
    pass


def checked_origin(origin):
    if not isinstance(origin, str):
        raise RemotePublisherError("HTTPS origin must be a string")
    try:
        uri = urlsplit(origin)
        port = uri.port or 443
    except ValueError as exc:
        raise RemotePublisherError("HTTPS URL contains an invalid port") from exc
    if (uri.scheme != "https" or not uri.hostname or uri.username is not None
            or uri.password is not None or uri.path not in ("", "/")
            or uri.query or uri.fragment or not 1 <= port <= 65535):
        raise RemotePublisherError("strict HTTPS root origin without credentials/query/fragment required")
    if any(ch.isspace() for ch in origin) or "\\" in origin:
        raise RemotePublisherError("malformed remote HTTPS URL")
    return uri.hostname, port


def secure_connection(origin, trusted_ca, server_sha256, *, timeout=30):
    host, port = checked_origin(origin)
    if not isinstance(server_sha256, str) or not SHA.fullmatch(server_sha256.lower()):
        raise RemotePublisherError("out-of-band server leaf SHA256 pin required")
    ca = Path(trusted_ca)
    if ca.is_symlink() or not ca.is_file() or ca.stat().st_size > 256_000:
        raise RemotePublisherError("unsafe trusted CA PEM")
    context = ssl.create_default_context(cafile=str(ca))
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    conn = http.client.HTTPSConnection(host, port, timeout=timeout, context=context)
    try:
        # Handshake verifies real HTTPS certificate chain + server hostname.
        # Do not load/send publisher token until the independent pin also passes.
        conn.connect()
        observed = hashlib.sha256(conn.sock.getpeercert(binary_form=True)).hexdigest()
        if not hmac.compare_digest(observed, server_sha256.lower()):
            raise RemotePublisherError("TLS server certificate does not match external pin")
    except BaseException:
        conn.close()
        raise
    return conn


def submit(candidate, artifact, publisher, token_file, origin, trusted_ca, server_sha256):
    # Pin and HTTPS CA verified BEFORE even reading the sensitive token file.
    transport = secure_connection(origin, trusted_ca, server_sha256)
    try:
        return local.submit(candidate, artifact, publisher, token_file,
                            port=checked_origin(origin)[1], verified_transport=transport)
    finally:
        transport.close()


def main():
    parser = argparse.ArgumentParser(description="Pinned TLS private publisher submission; no public release")
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--publisher", required=True)
    parser.add_argument("--token-file", type=Path, required=True)
    parser.add_argument("--origin", required=True)
    parser.add_argument("--trusted-ca-pem", type=Path, required=True)
    parser.add_argument("--server-cert-sha256", required=True)
    a = parser.parse_args()
    try:
        data = submit(a.candidate, a.artifact, a.publisher, a.token_file,
                      a.origin, a.trusted_ca_pem, a.server_cert_sha256)
    except (ValueError, OSError, ssl.SSLError, http.client.HTTPException) as exc:
        parser.exit(1, "REMOTE_TLS_PUBLISHER_UPLOAD_DENIED: " + str(exc) + "\n")
    print(json.dumps(data, sort_keys=True, separators=(",", ":")))
    print("TLS_PINNED_PRIVATE_QUARANTINE_ONLY; INDEPENDENT_PUBLISHER_IDENTITY_AND_RELEASE_REVIEW_REQUIRED")


if __name__ == "__main__":
    main()
