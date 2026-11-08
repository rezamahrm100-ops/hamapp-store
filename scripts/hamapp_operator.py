#!/usr/bin/env python3
"""Idempotent owner-controlled HamApp private publisher service lifecycle.

This is a ready-to-run operator adapter around the EXISTING private TLS inbox,
publisher token lifecycle and F-Droid release-review gates, not a second
publisher backend or a public approval server. Never stores secrets in GitHub.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import ssl
import stat
import struct
import subprocess
import sys
import tempfile

import private_publisher_inbox as inbox
import publisher_intake_service as gateway
import publisher_token_lifecycle as tokens
import remote_publisher_tls_service as remote

ROOT = Path(__file__).resolve().parents[1]
CONFIG = "service.json"
MAX_PEM = 256_000

class OperatorError(ValueError):
    pass

def private_root(path, *, created=False):
    if os.name != "posix":
        raise OperatorError("POSIX owner-private storage required; use the Docker service kit on Windows")
    p = Path(path).expanduser()
    if not p.is_absolute() or p.is_symlink():
        raise OperatorError("absolute non-symlink private data path required")
    if p.resolve() == ROOT or ROOT in p.resolve().parents:
        raise OperatorError("private data must be outside the public source checkout")
    if created:
        p = inbox._private_dir(p)
        if p.stat().st_nlink < 2:
            raise OperatorError("private data directory invalid")
        return p
    if p.exists():
        raise OperatorError("existing service data cannot be overwritten")
    if not p.parent.is_dir() or p.parent.is_symlink():
        raise OperatorError("private data parent must already exist")
    return p

def _pem(name, raw, *, private=False):
    if not isinstance(raw, bytes) or not 100 <= len(raw) <= MAX_PEM:
        raise OperatorError("TLS PEM input missing or too large")
    expected = (b"-----BEGIN " + (b"PRIVATE KEY" if private else b"CERTIFICATE") + b"-----")
    if expected not in raw and not (private and b"-----BEGIN RSA PRIVATE KEY-----" in raw):
        raise OperatorError("invalid TLS certificate/key PEM envelope")
    if b"\x00" in raw:
        raise OperatorError("binary input is not a TLS PEM")
    return raw

def load_pem_stdin(input_stream, *, with_token=False):
    """Read bounded PEM envelope and optional appended 64-byte secret from stdin."""
    header = input_stream.read(8)
    if len(header) != 8:
        raise OperatorError("cert/key stdin envelope missing")
    cert_size, key_size = struct.unpack("!II", header)
    if not (100 <= cert_size <= MAX_PEM and 100 <= key_size <= MAX_PEM):
        raise OperatorError("TLS PEM envelope lengths rejected")
    cert = input_stream.read(cert_size)
    key = input_stream.read(key_size)
    tail = input_stream.read(65 if with_token else 1)
    if len(cert) != cert_size or len(key) != key_size or (not with_token and tail):
        raise OperatorError("incomplete/oversized secret envelope")
    pair = (_pem("cert", cert), _pem("key", key, private=True))
    if with_token:
        return (*pair, validate_stdin_token(tail))
    return pair

def validate_stdin_token(raw):
    """Accept only an unlogged high-entropy token, never a URL or a line."""
    if (not isinstance(raw, bytes) or len(raw) != 64 or
            not all(c in b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for c in raw)):
        raise OperatorError("publisher token stdin must be exactly 64 URL-safe bytes")
    return raw.decode("ascii")

def read_token_stdin(stream):
    return validate_stdin_token(stream.read(65))

def read_pem_files(cert, key):
    public, secret = Path(cert), Path(key)
    if (public.is_symlink() or secret.is_symlink() or
            not public.is_file() or not secret.is_file()):
        raise OperatorError("TLS inputs must be non-symlink regular files")
    if public.resolve() == secret.resolve():
        raise OperatorError("TLS certificate and key must be different")
    return (
        _pem("cert", public.read_bytes()),
        _pem("key", secret.read_bytes(), private=True))

def fingerprint(cert):
    try:
        return hashlib.sha256(
            ssl.PEM_cert_to_DER_cert(cert.decode("ascii"))).hexdigest()
    except (ValueError, UnicodeError) as exc:
        raise OperatorError("invalid TLS public certificate") from exc

def local_development_certificate():
    """Generate a localhost-only TLS identity, NOT a production APK signer."""
    with tempfile.TemporaryDirectory(prefix="hamapp-dev-tls-") as tmp:
        directory = Path(tmp)
        certificate = directory / "localhost.pem"
        key = directory / "localhost.key"
        try:
            result = subprocess.run([
                "openssl", "req", "-new", "-x509", "-newkey", "rsa:2048",
                "-noenc", "-days", "365", "-subj", "/CN=localhost",
                "-addext", "subjectAltName=DNS:localhost,IP:127.0.0.1",
                "-keyout", str(key), "-out", str(certificate)
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
               check=False, timeout=35)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise OperatorError("local-only OpenSSL TLS setup unavailable") from exc
        if result.returncode:
            raise OperatorError("local-only TLS identity could not be generated")
        return certificate.read_bytes(), key.read_bytes()

def bootstrap(root, publisher, *, public_cert, private_key, local_development=False, first_token=None):
    """Provision first durable private service. Return one-time token once."""
    if not isinstance(publisher, str):
        raise OperatorError("publisher must be a string")
    tokens.validate_publisher(publisher)
    path = private_root(root)
    cert = _pem("cert", public_cert)
    key = _pem("key", private_key, private=True)
    pin = fingerprint(cert)
    # Validate the supplied matching pair BEFORE creating a service root.
    # We cannot load the SSL chain from bytes without an on-disk private file;
    # the private service will validate the pair immediately after writing.
    path.mkdir(mode=0o700)
    try:
        path.chmod(0o700)
        for label in ("inbox", "incoming"):
            (path / label).mkdir(mode=0o700)
        inbox._write_private(path / "tls-cert.pem", cert)
        inbox._write_private(path / "tls-key.pem", key)
        remote.certificate_files(path / "tls-cert.pem", path / "tls-key.pem")
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(str(path / "tls-cert.pem"), str(path / "tls-key.pem"))
        # The first token is displayed once. Only its hash is saved.
        token = gateway.provision(path / "credentials.json", publisher, token=first_token)
        config = {"schema_version": 1, "service": "hamapp-private-quarantine",
                  "port_default": 8766, "local_development_only": bool(local_development),
                  "tls_leaf_sha256": pin}
        inbox._write_private(path / CONFIG,
                             (json.dumps(config, sort_keys=True) + "\n").encode("utf-8"))
        check(path)
        return {"root": str(path), "publisher": publisher, "tls_leaf_sha256": pin,
                "one_time_token": token, "ready_for_private_quarantine": True,
                "real_publisher_identity_verified": False,
                "public_release_authorized": False}
    except BaseException:
        # Only remove a directory this function just created; never touch an
        # existing operator workspace on error.
        shutil.rmtree(path)
        raise

def check(root):
    path = private_root(root, created=True)
    config = gateway.private_file(path / CONFIG)
    data = json.loads(config.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != {
            "schema_version", "service", "port_default", "tls_leaf_sha256",
            "local_development_only"}:
        raise OperatorError("invalid private service configuration")
    if data["schema_version"] != 1 or data["service"] != "hamapp-private-quarantine":
        raise OperatorError("unexpected private service identity")
    if not isinstance(data["tls_leaf_sha256"], str):
        raise OperatorError("invalid TLS signing identity")
    cert, key = remote.certificate_files(path / "tls-cert.pem", path / "tls-key.pem")
    actual = fingerprint(cert.read_bytes())
    if actual != data["tls_leaf_sha256"]:
        raise OperatorError("TLS leaf changed without owner-pinned re-provisioning")
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=str(cert), keyfile=str(key))
    inbox._private_dir(path / "inbox")
    inbox._private_dir(path / "incoming")
    registrants = gateway.load_credentials(path / "credentials.json")
    return {"schema_version": 1, "service_ready": True,
            "publisher_token_slots": len(registrants),
            "tls_leaf_sha256": actual,
            "private_quarantine": True, "tls_chain_loaded": True,
            "local_development_only": data["local_development_only"],
            "server_running_proven": False,
            "owner_release_approved": False,
            "public_store_deployed": False}

def serve(root, *, host="127.0.0.1", port=8766, allow_public=False):
    info = check(root)
    path = private_root(root, created=True)
    if not 1 <= port <= 65535:
        raise OperatorError("invalid private server port")
    server = remote.TLSQuarantineServer(
        path / "inbox", path / "incoming", path / "credentials.json",
        path / "tls-cert.pem", path / "tls-key.pem",
        host=host, port=port, allow_public=allow_public)
    print("HAMAPP_PRIVATE_PUBLISHER_TLS_READY QUARANTINE_ONLY NO_RELEASE", flush=True)
    try:
        server.serve_forever(poll_interval=0.2)
    finally:
        server.server_close()

def change(root, action, publisher, *, token=None):
    check(root)
    path = private_root(root, created=True)
    return tokens.change_registry(path / "credentials.json", action, publisher, token=token)

def main(argv=None):
    p = argparse.ArgumentParser(description="HamApp one-backend private owner service")
    commands = p.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init")
    init.add_argument("--root", required=True, type=Path)
    init.add_argument("--publisher", required=True)
    choice = init.add_mutually_exclusive_group(required=True)
    choice.add_argument("--import-stdin", action="store_true")
    choice.add_argument("--dev-local-cert", action="store_true")
    choice.add_argument("--tls-cert", type=Path)
    init.add_argument("--tls-key", type=Path)
    init.add_argument("--token-stdin", action="store_true", required=False)
    probe = commands.add_parser("status")
    probe.add_argument("--root", required=True, type=Path)
    export = commands.add_parser("export-ca")
    export.add_argument("--root", required=True, type=Path)
    run = commands.add_parser("start")
    run.add_argument("--root", required=True, type=Path)
    run.add_argument("--host", default="127.0.0.1")
    run.add_argument("--port", type=int, default=8766)
    run.add_argument("--allow-public-bind", action="store_true")
    for name in ("add", "rotate", "revoke"):
        sub = commands.add_parser(name)
        sub.add_argument("--root", required=True, type=Path)
        sub.add_argument("--publisher", required=True)
        sub.add_argument("--token-stdin", action="store_true")
    opts = p.parse_args(argv)
    try:
        if opts.command == "init":
            if not opts.token_stdin:
                raise OperatorError("init requires caller-owned token on private stdin")
            if opts.dev_local_cert:
                if opts.tls_key is not None:
                    raise OperatorError("local TLS mode has no imported key")
                cert, key = local_development_certificate()
                first_token = read_token_stdin(sys.stdin.buffer)
            elif opts.import_stdin:
                if opts.tls_key is not None:
                    raise OperatorError("stdin import cannot specify an extra TLS key path")
                cert, key, first_token = load_pem_stdin(sys.stdin.buffer, with_token=True)
            else:
                if opts.tls_key is None:
                    raise OperatorError("TLS private key path missing")
                cert, key = read_pem_files(opts.tls_cert, opts.tls_key)
                first_token = read_token_stdin(sys.stdin.buffer)
            result = bootstrap(opts.root, opts.publisher,
                               public_cert=cert, private_key=key,
                               local_development=opts.dev_local_cert,
                               first_token=first_token)
            print("HAMAPP_PRIVATE_SERVICE_READY; NO_PUBLIC_RELEASE")
            print("PUBLISHER:", result["publisher"])
            print("TLS_LEAF_SHA256:", result["tls_leaf_sha256"])
        elif opts.command == "status":
            print(json.dumps(check(opts.root), sort_keys=True))
        elif opts.command == "export-ca":
            check(opts.root)
            path = private_root(opts.root, created=True)
            sys.stdout.write((path / "tls-cert.pem").read_text(encoding="ascii"))
        elif opts.command == "start":
            serve(opts.root, host=opts.host, port=opts.port,
                  allow_public=opts.allow_public_bind)
        else:
            if opts.command in ("add", "rotate") and not opts.token_stdin:
                raise OperatorError("token change requires caller-owned secret on stdin")
            token = read_token_stdin(sys.stdin.buffer) if opts.command in ("add", "rotate") else None
            change(opts.root, opts.command, opts.publisher, token=token)
            print("HAMAPP_PRIVATE_TOKEN_" + opts.command.upper() + "_SUCCESS")
        return 0
    except (OSError, ValueError, TypeError, ssl.SSLError) as ex:
        # Errors must not disclose certificate/key contents or token.
        p.exit(1, "HAMAPP_PRIVATE_OPERATOR_REJECTED: " + type(ex).__name__ + "\n")

if __name__ == "__main__":
    raise SystemExit(main())
