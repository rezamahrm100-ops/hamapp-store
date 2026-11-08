"""Owner-configurable Windows publisher transport.

Public package browsing requires no account. Optional publisher submissions
go ONLY to the existing private TLS quarantine API, never straight to a public
catalogue. A token is stored in per-user Windows DPAPI ciphertext, not code,
GitHub settings, environment variables, logs, or command-line arguments.
"""
import base64
import ctypes
from ctypes import wintypes
import hashlib
import hmac
import http.client
import json
import os
from pathlib import Path
import re
import ssl
import sys
import tempfile
from urllib.parse import urlsplit

SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
HEX = re.compile(r"[a-f0-9]{64}\Z")
SHA = re.compile(r"[a-f0-9]{40}\Z")
VERSION = re.compile(r"[0-9]+(?:\.[0-9]+){2}(?:-[0-9A-Za-z.-]+)?\Z")
MAX_BYTES = 512 * 1024 * 1024
MAX_META = 32768

class ConfigurationError(ValueError):
    pass

def profile_path():
    if sys.platform != "win32":
        raise ConfigurationError("Owner connection profile requires native Windows")
    root = os.environ.get("LOCALAPPDATA")
    if not root:
        raise ConfigurationError("Windows local application-data directory unavailable")
    return Path(root) / "HamAppStore" / "publisher-connection-v1.json"

def validate_profile(details, *, check_file=True):
    if not isinstance(details, dict) or set(details) != {
            "publisher", "origin", "trusted_ca", "server_cert_sha256"}:
        raise ConfigurationError("incomplete publisher connection settings")
    publisher = details["publisher"]
    origin = details["origin"]
    pin = details["server_cert_sha256"]
    ca = details["trusted_ca"]
    if not isinstance(publisher, str) or not SLUG.fullmatch(publisher):
        raise ConfigurationError("publisher identifier must be a simple repository name")
    if not isinstance(origin, str) or len(origin) > 512 or any(c.isspace() for c in origin):
        raise ConfigurationError("malformed HTTPS origin")
    try:
        parsed = urlsplit(origin)
        port = parsed.port or 443
    except ValueError as exc:
        raise ConfigurationError("invalid TLS server port") from exc
    if (parsed.scheme != "https" or not parsed.hostname or not 1 <= port <= 65535
            or parsed.username is not None or parsed.password is not None
            or parsed.query or parsed.fragment or parsed.path not in ("", "/")
            or "\\" in origin):
        raise ConfigurationError("HTTPS host-only origin required; no inline credentials")
    if not isinstance(pin, str) or not HEX.fullmatch(pin.lower()):
        raise ConfigurationError("independently verified server certificate SHA256 is required")
    if not isinstance(ca, str) or not 1 <= len(ca) <= 2048:
        raise ConfigurationError("choose a trusted CA public certificate")
    file = Path(ca)
    if check_file and (file.is_symlink() or not file.is_file() or file.stat().st_size > 256000):
        raise ConfigurationError("trusted CA PEM must be a small regular local file")
    return {"publisher": publisher, "origin": origin, "trusted_ca": str(file),
            "server_cert_sha256": pin.lower()}

def valid_token(value):
    if (not isinstance(value, str) or not 64 <= len(value) <= 128
            or any(ch.isspace() for ch in value)):
        raise ConfigurationError("publisher token must be a 64-128 character private secret")
    return value

class _Blob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD),
                ("pbData", ctypes.POINTER(ctypes.c_ubyte))]

def _dpapi(data, *, unprotect=False):
    if sys.platform != "win32":
        raise ConfigurationError("Windows user-only DPAPI is required")
    if not isinstance(data, bytes) or not data:
        raise ConfigurationError("empty secret")
    crypt = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    function = crypt.CryptUnprotectData if unprotect else crypt.CryptProtectData
    if unprotect:
        function.argtypes = [ctypes.POINTER(_Blob), ctypes.c_void_p,
                             ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                             wintypes.DWORD, ctypes.POINTER(_Blob)]
    else:
        function.argtypes = [ctypes.POINTER(_Blob), ctypes.c_wchar_p,
                             ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                             wintypes.DWORD, ctypes.POINTER(_Blob)]
    function.restype = wintypes.BOOL
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    src_buf = ctypes.create_string_buffer(data)
    source = _Blob(len(data), ctypes.cast(src_buf, ctypes.POINTER(ctypes.c_ubyte)))
    destination = _Blob()
    args = ([ctypes.byref(source), None, None, None, None, 0x1,
             ctypes.byref(destination)] if unprotect else
            [ctypes.byref(source), "HamApp publisher authorization", None,
             None, None, 0x1, ctypes.byref(destination)])
    if not function(*args):
        raise ConfigurationError("DPAPI could not protect or recover the account token")
    try:
        return ctypes.string_at(destination.pbData, destination.cbData)
    finally:
        kernel.LocalFree(ctypes.cast(destination.pbData, ctypes.c_void_p))

def read_profile(*, path=None):
    path = Path(path) if path is not None else profile_path()
    if not path.exists():
        return None
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 8192:
        raise ConfigurationError("unsafe owner connection profile")
    record = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(record, dict) or set(record) !=
            {"schema_version", "details", "encrypted_token"} or
            record["schema_version"] != 1 or
            not isinstance(record["encrypted_token"], str)):
        raise ConfigurationError("invalid owner connection file")
    record["details"] = validate_profile(record["details"])
    if not 0 < len(record["encrypted_token"]) < 4096:
        raise ConfigurationError("encrypted secret is invalid")
    return record

def save_profile(details, token="", *, path=None):
    if sys.platform != "win32":
        raise ConfigurationError("Windows user-only secure storage required")
    validated = validate_profile(details)
    path = Path(path) if path is not None else profile_path()
    if path.is_symlink():
        raise ConfigurationError("cannot overwrite a symbolic-link profile")
    if token:
        encrypted = base64.b64encode(_dpapi(valid_token(token).encode("utf-8"))).decode("ascii")
    else:
        previous = read_profile(path=path)
        if previous is None:
            raise ConfigurationError("enter the account token on first setup")
        encrypted = previous["encrypted_token"]
    if path.parent.is_symlink():
        raise ConfigurationError("unsafe profile directory")
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"schema_version": 1, "details": validated, "encrypted_token": encrypted}
    content = (json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    temp = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".connection-",
                                         suffix=".tmp", delete=False) as handle:
            temp = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        if temp is not None and temp.exists():
            temp.unlink()
    return validated

def remove_profile(*, path=None):
    path = Path(path) if path is not None else profile_path()
    if path.is_symlink():
        raise ConfigurationError("unsafe profile")
    if path.exists():
        path.unlink()

def _connection(details):
    cfg = validate_profile(details)
    parsed = urlsplit(cfg["origin"])
    context = ssl.create_default_context(cafile=cfg["trusted_ca"])
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.verify_mode = ssl.CERT_REQUIRED
    context.check_hostname = True
    conn = http.client.HTTPSConnection(parsed.hostname, parsed.port or 443,
                                       context=context, timeout=20)
    try:
        conn.connect()
        actual = hashlib.sha256(conn.sock.getpeercert(binary_form=True)).hexdigest()
        if not hmac.compare_digest(actual, cfg["server_cert_sha256"]):
            raise ConfigurationError("server certificate fingerprint does not match trusted pin")
        return conn
    except BaseException:
        conn.close()
        raise

def probe(details):
    """Read-only TLS+service reachability. Does not claim token or identity approval."""
    conn = _connection(details)
    try:
        # Existing quarantine protocol intentionally disables GET and returns 405.
        conn.request("GET", "/v1/submissions", headers={"Accept": "application/json"})
        reply = conn.getresponse()
        raw = reply.read(8193)
        if len(raw) > 8192 or reply.status != 405:
            raise ConfigurationError("endpoint does not match the private quarantine API")
        result = json.loads(raw.decode("utf-8"))
        if result != {"error": "read_api_disabled"}:
            raise ConfigurationError("unknown publisher server response")
        return {"tls_pinned": True, "quarantine_api_reachable": True,
                "publisher_token_authenticated": False,
                "production_release_authorized": False}
    finally:
        conn.close()

def validate_candidate(candidate_path, artifact_path, publisher):
    """Conservative local validation before disclosing token/uploading bytes."""
    candidate_path = Path(candidate_path)
    artifact_path = Path(artifact_path)
    if (candidate_path.is_symlink() or not candidate_path.is_file() or
            candidate_path.stat().st_size > MAX_META or
            artifact_path.is_symlink() or not artifact_path.is_file()):
        raise ConfigurationError("input files must be regular files, not links")
    raw = candidate_path.read_bytes()
    if not 0 < len(raw) <= MAX_META:
        raise ConfigurationError("candidate metadata size invalid")
    candidate = json.loads(raw.decode("utf-8"))
    if (not isinstance(candidate, dict) or set(candidate) !=
            {"release", "source_repo", "source_sha", "package_id", "version_code"} or
            candidate["source_repo"] != publisher or
            not isinstance(candidate["source_sha"], str) or
            not SHA.fullmatch(candidate["source_sha"].lower())):
        raise ConfigurationError("unrecognized publisher/source claim")
    release = candidate["release"]
    if not isinstance(release, dict) or set(release) != {
            "app_id", "platform", "version", "asset_url", "sha256", "size_bytes"}:
        raise ConfigurationError("release metadata schema invalid")
    if (not isinstance(release["app_id"], str) or not SLUG.fullmatch(release["app_id"])
            or release["platform"] not in ("android", "windows")
            or not isinstance(release["version"], str) or not VERSION.fullmatch(release["version"])
            or not isinstance(release["sha256"], str) or not HEX.fullmatch(release["sha256"])
            or type(release["size_bytes"]) is not int
            or not 0 < release["size_bytes"] <= MAX_BYTES):
        raise ConfigurationError("invalid package release fields")
    parsed = urlsplit(release["asset_url"])
    parts = parsed.path.strip("/").split("/")
    if (parsed.scheme != "https" or parsed.hostname != "github.com"
            or parsed.username or parsed.password or parsed.port is not None
            or parsed.query or parsed.fragment or len(parts) != 6
            or parts[:4] != ["rezamahrm100-ops", publisher, "releases", "download"]
            or parts[4] not in (release["version"], "v" + release["version"])
            or "%" in parsed.path or "\\" in parsed.path):
        raise ConfigurationError("binary must be from the declared official release")
    expected_suffix = (".apk",) if release["platform"] == "android" else (
        ".exe", ".msi", ".msix", ".msixbundle")
    if (not artifact_path.name.lower().endswith(expected_suffix) or
            not parts[-1].lower().endswith(expected_suffix) or
            artifact_path.suffix.lower() != Path(parts[-1]).suffix.lower()):
        raise ConfigurationError("binary extension does not match release")
    if release["platform"] == "android":
        if (not isinstance(candidate["package_id"], str) or
                not re.fullmatch(r"[a-zA-Z]\w*(?:\.[a-zA-Z]\w*)+", candidate["package_id"]) or
                type(candidate["version_code"]) is not int or
                not 1 <= candidate["version_code"] < 2**31):
            raise ConfigurationError("invalid Android package identity")
    elif candidate["package_id"] is not None or candidate["version_code"] is not None:
        raise ConfigurationError("unexpected Windows package fields")
    sha = hashlib.sha256()
    size = 0
    with artifact_path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            size += len(block)
            if size > MAX_BYTES: raise ConfigurationError("candidate too large")
            sha.update(block)
    if size != release["size_bytes"] or not hmac.compare_digest(
            sha.hexdigest(), release["sha256"]):
        raise ConfigurationError("local file does not match candidate hash/size")
    return raw, release

def submit(candidate, artifact, *, path=None):
    """Explicitly send exact signed-candidate claim to a private REVIEW queue only."""
    record = read_profile(path=path)
    if record is None:
        raise ConfigurationError("configure and save publisher profile first")
    details = record["details"]
    raw, release = validate_candidate(candidate, artifact, details["publisher"])
    # CA+hostname+out-of-band exact leaf pin MUST pass before decrypting the token.
    conn = _connection(details)
    try:
        ciphertext = base64.b64decode(record["encrypted_token"], validate=True)
        secret = valid_token(_dpapi(ciphertext, unprotect=True).decode("utf-8"))
        encoded = base64.b64encode(raw).decode("ascii")
        if len(encoded) > 46000:
            raise ConfigurationError("candidate metadata exceeds API header")
        conn.putrequest("POST", "/v1/submissions")
        conn.putheader("Content-Type", "application/octet-stream")
        conn.putheader("Content-Length", str(release["size_bytes"]))
        conn.putheader("Authorization", "Bearer " + secret)
        conn.putheader("X-HamApp-Publisher", details["publisher"])
        conn.putheader("X-HamApp-Candidate-Base64", encoded)
        conn.endheaders()
        actual = hashlib.sha256()
        count = 0
        with Path(artifact).open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                actual.update(block)
                count += len(block)
                if count > release["size_bytes"]:
                    raise ConfigurationError("input changed during transfer")
                conn.send(block)
        if (count != release["size_bytes"] or not hmac.compare_digest(
                actual.hexdigest(), release["sha256"])):
            raise ConfigurationError("artifact mutated during upload")
        response = conn.getresponse()
        payload = response.read(8193)
        if len(payload) > 8192 or response.status != 202:
            raise ConfigurationError("private quarantine rejected the submission")
        info = json.loads(payload.decode("utf-8"))
        if (info.get("status") != "quarantined" or
                info.get("local_token_authenticated") is not True or
                info.get("publisher_identity_independently_verified") is not False or
                info.get("owner_review_approved") is not False or
                info.get("public_distribution_authorized") is not False):
            raise ConfigurationError("quarantine response not trustworthy")
        validate_candidate(candidate, artifact, details["publisher"])
        return {"submission_id": info["submission_id"], "status": "quarantined",
                "production_release_authorized": False}
    finally:
        conn.close()
