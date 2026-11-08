#!/usr/bin/env python3
"""Loopback-only, token-authenticated private publisher drop-off.

This is a LOCAL transport boundary, not an Internet-facing portal, a verified
developer identity, an owner approval, or a release publishing operation.
No submitted bytes or credentials are ever uploaded to GitHub.
"""
import argparse
import base64
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import stat
import tempfile
from urllib.parse import urlsplit

import private_publisher_inbox as inbox
import release_integrity

MAX_UPLOAD = 512 * 1024 * 1024
MAX_CANDIDATE_HEADER = 46000
MAX_SUBMISSIONS_PER_PUBLISHER = 100
MAX_BYTES_PER_PUBLISHER = 2 * 1024 * 1024 * 1024
HASH = re.compile(r"[a-f0-9]{64}\Z")


class IntakeServiceError(ValueError):
    pass


def private_file(path):
    if os.name != "posix":
        raise IntakeServiceError("local gateway requires POSIX permissions")
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise IntakeServiceError("credential file must be a regular non-symlink")
    info = path.stat()
    if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
            or info.st_uid != os.geteuid() or info.st_mode & 0o077):
        raise IntakeServiceError("credential file must be owner-owned and mode 0600")
    resolved = path.resolve(strict=True)
    if resolved == inbox.PROJECT_ROOT or inbox.PROJECT_ROOT in resolved.parents:
        raise IntakeServiceError("credentials cannot reside in public source checkout")
    if info.st_size > 32768:
        raise IntakeServiceError("credential file too large")
    return path


def load_credentials(path):
    raw = json.loads(private_file(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or set(raw) != {"schema_version", "publishers"} or raw["schema_version"] != 1:
        raise IntakeServiceError("invalid credential registry schema")
    publishers = raw["publishers"]
    if not isinstance(publishers, list) or not 0 <= len(publishers) <= 100:
        raise IntakeServiceError("invalid publisher credential count")
    result = {}
    for item in publishers:
        if not isinstance(item, dict) or set(item) != {"source_repo", "token_sha256"}:
            raise IntakeServiceError("invalid publisher credentials")
        name, digest = item["source_repo"], item["token_sha256"]
        if (not isinstance(name, str) or not release_integrity.ID.fullmatch(name)
                or not isinstance(digest, str) or not HASH.fullmatch(digest)
                or name in result or digest in result.values()):
            raise IntakeServiceError("duplicate or invalid publisher credential")
        result[name] = digest
    return result


def provision(path, publisher, *, token=None):
    """Create first registry with a caller-owned secret, or a random library token."""
    if os.name != "posix" or not isinstance(publisher, str) or not release_integrity.ID.fullmatch(publisher):
        raise IntakeServiceError("POSIX and valid publisher source repository required")
    path = Path(path)
    if path.exists() or path.is_symlink():
        raise IntakeServiceError("never overwrite an existing credential registry")
    resolved = path.resolve()
    if resolved == inbox.PROJECT_ROOT or inbox.PROJECT_ROOT in resolved.parents:
        raise IntakeServiceError("credentials cannot be committed to public repository")
    parent = inbox._private_dir(path.parent)
    if token is None:
        token = secrets.token_urlsafe(48)
    if not isinstance(token, str) or not re.fullmatch(r"[A-Za-z0-9_-]{64}", token):
        raise IntakeServiceError("publisher token must be 64 characters of secure URL-safe entropy")
    payload = json.dumps({
        "schema_version": 1,
        "publishers": [{"source_repo": publisher,
                        "token_sha256": hashlib.sha256(token.encode("ascii")).hexdigest()}]
    }, sort_keys=True).encode("utf-8") + b"\n"
    inbox._write_private(parent / path.name, payload)
    return token


def quota(root, publisher, new_size):
    """Bound owner-local storage without trusting any remote quota request."""
    total, count = 0, 0
    entries = list(Path(root).iterdir())
    if len(entries) > 10000:
        raise IntakeServiceError("too many private submissions; owner maintenance required")
    for item in entries:
        if not inbox.ID.fullmatch(item.name):
            raise IntakeServiceError("unexpected private root entry")
        folder, receipt = inbox.load(root, item.name)
        if folder.parent != Path(root).resolve():
            raise IntakeServiceError("submission directory containment failed")
        if receipt.get("claimed_publisher") == publisher:
            count += 1
            size = receipt.get("artifact_size_bytes")
            if type(size) is not int or size < 1:
                raise IntakeServiceError("malformed private quota evidence")
            total += size
    if count >= MAX_SUBMISSIONS_PER_PUBLISHER or total + new_size > MAX_BYTES_PER_PUBLISHER:
        raise IntakeServiceError("publisher private intake quota exhausted")


class LocalIntakeServer(HTTPServer):
    allow_reuse_address = False

    def __init__(self, root, temp_dir, credentials, host="127.0.0.1", port=0):
        if host != "127.0.0.1":
            raise IntakeServiceError("public-network binding is forbidden")
        self.quarantine_root = inbox._private_dir(root)
        self.temp_dir = inbox._private_dir(temp_dir)
        if self.temp_dir == self.quarantine_root or self.quarantine_root in self.temp_dir.parents:
            raise IntakeServiceError("temporary uploads must be outside the quarantine root")
        self.credential_file = private_file(credentials)
        self.credentials = load_credentials(self.credential_file)
        super().__init__((host, port), IntakeHandler)


class IntakeHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def log_message(self, _format, *_args):
        # Never log tokens, submitted package names, private IDs or headers.
        return

    def _reply(self, status, value):
        raw = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(raw)
        self.close_connection = True

    def do_GET(self):
        self._reply(405, {"error": "read_api_disabled"})

    def do_POST(self):
        if self.path != "/v1/submissions":
            self._reply(404, {"error": "unknown_endpoint"})
            return
        claimed = self.headers.get("X-HamApp-Publisher", "")
        bearer = self.headers.get("Authorization", "")
        if (not release_integrity.ID.fullmatch(claimed)
                or not bearer.startswith("Bearer ")
                or len(bearer) > 150 or len(bearer) < 40):
            self._reply(401, {"error": "unauthorized"})
            return
        # Reopen the private atomic registry on EVERY authenticated request:
        # operator revocation and rotation become effective immediately,
        # without reusing a stale startup credential snapshot.
        try:
            current_credentials = load_credentials(self.server.credential_file)
        except (ValueError, OSError, UnicodeError):
            self._reply(503, {"error": "publisher_auth_registry_unavailable"})
            return
        observed = hashlib.sha256(bearer[7:].encode("utf-8")).hexdigest()
        expected = current_credentials.get(claimed, "0" * 64)
        if not hmac.compare_digest(observed, expected) or claimed not in current_credentials:
            self._reply(401, {"error": "unauthorized"})
            return
        encoded = self.headers.get("X-HamApp-Candidate-Base64", "")
        raw_length = self.headers.get("Content-Length", "")
        if (self.headers.get("Transfer-Encoding") or
                self.headers.get("Content-Type") != "application/octet-stream"
                or not raw_length.isascii() or not raw_length.isdigit()
                or not 1 <= len(raw_length) <= 10 or not 0 < int(raw_length) <= MAX_UPLOAD
                or len(encoded) > MAX_CANDIDATE_HEADER):
            self._reply(422, {"error": "invalid_upload_envelope"})
            return
        try:
            meta_bytes = base64.b64decode(encoded, validate=True)
            if not 0 < len(meta_bytes) <= inbox.MAX_METADATA:
                raise IntakeServiceError("metadata size rejected")
            candidate = json.loads(meta_bytes.decode("utf-8"))
            release = inbox.validate_claim(candidate, claimed)
            size = int(raw_length)
            if size != release["size_bytes"]:
                raise IntakeServiceError("declared binary size mismatch")
            quota(self.server.quarantine_root, claimed, size)
            ext = Path(urlsplit(release["asset_url"]).path).suffix.lower()
            with tempfile.TemporaryDirectory(prefix="hamapp-incoming-", dir=self.server.temp_dir) as tmp:
                path = Path(tmp) / ("candidate" + ext)
                fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
                digest = hashlib.sha256()
                with os.fdopen(fd, "wb") as destination:
                    remaining = size
                    self.connection.settimeout(30)
                    while remaining:
                        part = self.rfile.read(min(1024 * 1024, remaining))
                        if not part:
                            raise IntakeServiceError("truncated upload")
                        destination.write(part)
                        digest.update(part)
                        remaining -= len(part)
                    destination.flush()
                    os.fsync(destination.fileno())
                if not hmac.compare_digest(digest.hexdigest(), release["sha256"]):
                    raise IntakeServiceError("binary digest mismatch")
                result = inbox.stage(self.server.quarantine_root, candidate, path, claimed)
            self._reply(202, {
                "submission_id": result["submission_id"],
                "status": "quarantined",
                "local_token_authenticated": True,
                "publisher_identity_independently_verified": False,
                "owner_review_approved": False,
                "public_distribution_authorized": False
            })
        except (ValueError, TypeError, KeyError, OSError, UnicodeError, base64.binascii.Error):
            self._reply(422, {"error": "quarantine_rejected"})


def main():
    parser = argparse.ArgumentParser(description="Owner-only LOCAL publisher gateway; no release")
    modes = parser.add_subparsers(dest="action", required=True)
    first = modes.add_parser("provision")
    first.add_argument("--credential-file", required=True, type=Path)
    first.add_argument("--publisher", required=True)
    serve = modes.add_parser("serve")
    serve.add_argument("--root", required=True, type=Path)
    serve.add_argument("--temp-dir", required=True, type=Path)
    serve.add_argument("--credential-file", required=True, type=Path)
    serve.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    try:
        if args.action == "provision":
            token = provision(args.credential_file, args.publisher)
            print("LOCAL_TOKEN_ONE_TIME_SHOW:", token)
            print("KEEP_SECRET_OFF_GITHUB; NOT_PRODUCTION_PUBLISHER_APPROVAL")
        else:
            if not 1 <= args.port <= 65535:
                raise IntakeServiceError("invalid local port")
            server = LocalIntakeServer(args.root, args.temp_dir, args.credential_file, port=args.port)
            print("LOCAL_QUARANTINE_INGEST_LISTENING_ON_LOOPBACK_ONLY; NO_PUBLICATION", flush=True)
            try:
                server.serve_forever(poll_interval=0.5)
            finally:
                server.server_close()
    except (ValueError, OSError, UnicodeError) as exc:
        parser.exit(1, "LOCAL_PUBLISHER_GATEWAY_REJECTED: " + str(exc) + "\n")


if __name__ == "__main__":
    main()
