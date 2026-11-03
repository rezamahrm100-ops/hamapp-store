#!/usr/bin/env python3
"""TLS-only publisher quarantine ingress, never an automatic publisher approval.

Makes the existing POSIX owner-private quarantine and exact-byte review available
behind a mandatory, operator-supplied TLS certificate. Browser-grade public
identity, MFA, moderation, production deployment and publication are separate
owner-operated gates; this API never performs those actions.

No HTTPS server private key, token, binary, or candidate is stored in git.
"""
import argparse
from http.server import HTTPServer
import ipaddress
import os
from pathlib import Path
import socket
import socketserver
import ssl
import threading

import private_publisher_inbox as inbox
from publisher_intake_service import (
    IntakeHandler, IntakeServiceError, load_credentials, private_file
)


def checked_bind(host, *, allow_public):
    if not isinstance(host, str) or not host:
        raise IntakeServiceError("explicit IPv4 interface required")
    try:
        address = ipaddress.ip_address(host)
    except ValueError as exc:
        raise IntakeServiceError("listener must be an explicit IPv4 address") from exc
    if address.version != 4 or address.is_multicast or address.is_unspecified and not allow_public:
        raise IntakeServiceError("unsafe network interface")
    if not address.is_loopback and not allow_public:
        raise IntakeServiceError("external HTTPS binding requires explicit operator opt-in")
    return host


def certificate_files(cert_file, key_file):
    cert = Path(cert_file)
    key = private_file(key_file)
    if cert.is_symlink() or not cert.is_file() or cert.stat().st_size > 256_000:
        raise IntakeServiceError("invalid or unbounded TLS public certificate")
    if cert.resolve(strict=True) == key.resolve(strict=True):
        raise IntakeServiceError("TLS certificate and private key must be distinct")
    return cert, key


class LimitedThreadingMixIn(socketserver.ThreadingMixIn):
    """Hard cap sockets/workers and release limit after every request."""
    daemon_threads = True
    block_on_close = True
    request_queue_size = 8
    MAX_WORKERS = 8

    def process_request(self, request, client_address):
        if not self._workers.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self._workers.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._workers.release()


class RemoteHandler(IntakeHandler):
    """Reuse the exact auth/hash/quarantine endpoint, never expose review API."""
    def do_POST(self):
        # Existing intake quotas are checked before staging. Serializing the
        # complete bounded upload prevents races that would evade tenant quotas
        # when multiple publisher clients submit at the same instant.
        if not self.server.ingest_lock.acquire(blocking=False):
            self._reply(503, {"error": "ingest_busy_retry"})
            return
        try:
            return super().do_POST()
        finally:
            self.server.ingest_lock.release()

    def do_GET(self):
        return super().do_GET()

    def do_PUT(self):
        self._reply(405, {"error": "method_not_allowed"})

    def do_DELETE(self):
        self._reply(405, {"error": "method_not_allowed"})

    def do_PATCH(self):
        self._reply(405, {"error": "method_not_allowed"})


class TLSQuarantineServer(LimitedThreadingMixIn, HTTPServer):
    allow_reuse_address = False

    def __init__(self, root, temp_dir, credentials, cert_file, key_file,
                 *, host="127.0.0.1", port=0, allow_public=False):
        if os.name != "posix":
            raise IntakeServiceError("private POSIX owner-only quarantine is required")
        host = checked_bind(host, allow_public=allow_public)
        self.quarantine_root = inbox._private_dir(root)
        self.temp_dir = inbox._private_dir(temp_dir)
        if (self.temp_dir == self.quarantine_root
                or self.quarantine_root in self.temp_dir.parents
                or self.temp_dir in self.quarantine_root.parents):
            raise IntakeServiceError("private upload temporary storage must be isolated")
        self.credential_file = private_file(credentials)
        self.credentials = load_credentials(self.credential_file)
        cert, key = certificate_files(cert_file, key_file)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.options |= getattr(ssl, "OP_NO_COMPRESSION", 0)
        context.options |= getattr(ssl, "OP_NO_RENEGOTIATION", 0)
        context.load_cert_chain(certfile=str(cert), keyfile=str(key))
        self.ingest_lock = threading.Lock()
        self._workers = threading.BoundedSemaphore(self.MAX_WORKERS)
        super().__init__((host, port), RemoteHandler, bind_and_activate=False)
        try:
            self.socket = context.wrap_socket(self.socket, server_side=True,
                                             do_handshake_on_connect=False)
            self.server_bind()
            self.server_activate()
        except Exception:
            self.server_close()
            raise

    def get_request(self):
        conn, address = self.socket.accept()
        # Bounded TLS handshake/header wait; inherited streaming upload handler
        # separately bounds body read, exact Content-Length and cryptographic SHA.
        conn.settimeout(12)
        try:
            conn.do_handshake()
        except (ssl.SSLError, TimeoutError, OSError):
            conn.close()
            raise
        return conn, address


def main():
    parser = argparse.ArgumentParser(description="Operator-managed remote HTTPS intake; quarantine only")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--temp-dir", type=Path, required=True)
    parser.add_argument("--credential-file", type=Path, required=True)
    parser.add_argument("--tls-cert", type=Path, required=True)
    parser.add_argument("--tls-key", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--allow-public-bind", action="store_true", default=False)
    args = parser.parse_args()
    try:
        if not 1 <= args.port <= 65535:
            raise IntakeServiceError("invalid TLS listener port")
        server = TLSQuarantineServer(
            args.root, args.temp_dir, args.credential_file, args.tls_cert,
            args.tls_key, host=args.host, port=args.port,
            allow_public=args.allow_public_bind)
        print("HTTPS_PUBLISHER_QUARANTINE_ONLY; INDEPENDENT_IDENTITY_AND_OWNER_APPROVAL_NOT_GRANTED",
              flush=True)
        try:
            server.serve_forever(poll_interval=0.2)
        finally:
            server.server_close()
    except (OSError, ValueError, ssl.SSLError) as exc:
        parser.exit(1, "REMOTE_TLS_QUARANTINE_REFUSED: " + str(exc) + "\n")


if __name__ == "__main__":
    main()
