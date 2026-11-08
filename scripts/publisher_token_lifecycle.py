#!/usr/bin/env python3
"""Owner-only private publisher token add, rotate, revoke and fail-closed reload.

NO network admin endpoint. Never uploads secrets, creates an account, proves a
person is a developer or approves a release. Registry lives OUTSIDE GitHub.
"""
import argparse
try:
    import fcntl  # POSIX-only actual cross-process advisory file lock
except ImportError:
    fcntl = None  # Windows source CI may import but must never run operator CLI
import hashlib
import json
import os
import re
import sys
from pathlib import Path
import secrets
import stat
import tempfile

import private_publisher_inbox as inbox
import publisher_intake_service as gateway
import release_integrity


class CredentialOperationError(ValueError):
    pass


def validate_publisher(name):
    if not isinstance(name, str) or not release_integrity.ID.fullmatch(name):
        raise CredentialOperationError("invalid publisher ID")
    return name


def _secure_owner_lock(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise CredentialOperationError("credential lock must be a real file")
    info = path.stat()
    if not (stat.S_ISREG(info.st_mode) and info.st_nlink == 1
            and info.st_uid == os.geteuid() and not info.st_mode & 0o077):
        raise CredentialOperationError("unsafe publisher registry lock")
    return path


def change_registry(path, action, publisher, *, token=None):
    """Linearizable mutation; optional caller-held secret avoids log disclosure."""
    if os.name != "posix" or action not in ("add", "rotate", "revoke"):
        raise CredentialOperationError("owner-controlled POSIX lifecycle action required")
    publisher = validate_publisher(publisher)
    registry = gateway.private_file(path)
    parent = inbox._private_dir(registry.parent)
    if registry.resolve(strict=True).parent != parent:
        raise CredentialOperationError("registry must stay in private parent directory")
    lock_path = parent / (registry.name + ".lock")
    if lock_path.is_symlink():
        raise CredentialOperationError("unsafe publisher token lock path")
    # Concurrent owner-admin processes use the same stable lock inode.
    # Never truncate, follow a symbolic link or reuse a non-private lock.
    flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(lock_path, flags, 0o600)
    with os.fdopen(descriptor, "r+b") as lock:
        info = os.fstat(lock.fileno())
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                or info.st_uid != os.geteuid() or info.st_mode & 0o077):
            raise CredentialOperationError("private lock must be owner-owned 0600 regular inode")
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            # Reopen *inside* file lock. One immutable lock identity prevents
            # concurrent add/rotate/revoke from overwriting another change.
            observed = gateway.load_credentials(registry)
            if action == "add":
                if publisher in observed or len(observed) >= 100:
                    raise CredentialOperationError("publisher already exists or quota full")
            else:
                if publisher not in observed:
                    raise CredentialOperationError("publisher is not enrolled")
            secret = None
            if action in ("add", "rotate"):
                secret = token if token is not None else secrets.token_urlsafe(48)
                if not isinstance(secret, str) or not re.fullmatch(r"[A-Za-z0-9_-]{64}", secret):
                    raise CredentialOperationError("invalid externally supplied publisher token")
                digest = hashlib.sha256(secret.encode("ascii")).hexdigest()
                if digest in observed.values():
                    raise CredentialOperationError("unexpected duplicate token digest")
                observed[publisher] = digest
            else:
                del observed[publisher]
            payload = {
                "schema_version": 1,
                "publishers": [
                    {"source_repo": name, "token_sha256": digest}
                    for name, digest in sorted(observed.items())
                ],
            }
            raw = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
            if len(raw) > 32768:
                raise CredentialOperationError("credential registry too large")
            # Durable atomic replace under private 0700 parent. A reader sees
            # either fully valid previous registry or fully valid successor.
            descriptor, temporary = tempfile.mkstemp(prefix=".hamapp-token-",
                                                     dir=parent)
            try:
                os.fchmod(descriptor, 0o600)
                with os.fdopen(descriptor, "wb") as destination:
                    destination.write(raw)
                    destination.flush()
                    os.fsync(destination.fileno())
                os.replace(temporary, registry)
                directory_fd = os.open(parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
            if gateway.load_credentials(registry) != observed:
                raise CredentialOperationError("private mutation readback mismatch")
            return {"action": action, "publisher": publisher,
                    "one_time_secret": secret,
                    "live_revocation_supported": True,
                    "publisher_identity_independently_verified": False,
                    "owner_publication_approved": False}
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def main():
    parser = argparse.ArgumentParser(description="Private POSIX operator token lifecycle")
    parser.add_argument("action", choices=("add", "rotate", "revoke"))
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--publisher", required=True)
    parser.add_argument("--token-stdin", action="store_true")
    args = parser.parse_args()
    try:
        caller_token = None
        if args.action in ("add", "rotate"):
            if not args.token_stdin:
                raise CredentialOperationError("private stdin required for token lifecycle")
            value = sys.stdin.buffer.read(65)
            if not re.fullmatch(rb"[A-Za-z0-9_-]{64}", value):
                raise CredentialOperationError("invalid private token stdin envelope")
            caller_token = value.decode("ascii")
        receipt = change_registry(args.registry, args.action, args.publisher, token=caller_token)
    except (ValueError, OSError, UnicodeError) as exc:
        parser.exit(1, "PRIVATE_PUBLISHER_TOKEN_ADMIN_REFUSED: " + str(exc) + "\n")
    print("OWNER_PRIVATE_PUBLISHER_TOKEN_" + args.action.upper() + "_COMMITTED")
    print("NOT_LEGAL_PUBLISHER_IDENTITY; NOT_A_PUBLIC_RELEASE_APPROVAL")


if __name__ == "__main__":
    main()
