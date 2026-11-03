#!/usr/bin/env python3
"""Genuine disposable Microsoft PE/Authenticode cryptographic acceptance.

Only a GitHub-hosted Linux runner with the exact unsigned native Windows
PyInstaller artifact may call this. Real osslsigncode/OpenSSL signing and
verification, never mock receipts, no owner certificates, no public releases.
All temporary PFX, passwords, signatures and EXEs are deleted before upload.
"""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import tempfile

MAX_BYTES = 200 * 1024 * 1024
SOURCE_SHA = re.compile(r"[a-f0-9]{40}\Z")


class AuthenticodeDrillError(ValueError):
    pass


def exact_sha256(path):
    digest, size = hashlib.sha256(), 0
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    if not 1000 <= size <= MAX_BYTES:
        raise AuthenticodeDrillError("actual Windows PE size outside bounded test range")
    return digest.hexdigest(), size


def run(command, expected_success=True, phase="unspecified"):
    """No shell, no credential arguments, bounded actual subprocess execution."""
    try:
        completed = subprocess.run(command, capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=90,
                                   check=False)
    except (subprocess.TimeoutExpired, OSError) as exc:
        raise AuthenticodeDrillError("upstream Authenticode tool unavailable or timed out") from exc
    ok = completed.returncode == 0
    if ok != expected_success:
        # Never expose upstream messages that might echo paths, key passwords,
        # signing identities or user-controlled metadata into logs.
        diagnostic = ""
        # Verification (never signing) deals only with PUBLIC disposable
        # test certificates. Emit bounded, sanitized public status hints.
        if phase.startswith("verify-"):
            public_hints = []
            for line in (completed.stdout + "\n" + completed.stderr).splitlines():
                lowered = line.lower()
                if any(word in lowered for word in (
                        "verification", "error", "unable", "trust", "chain",
                        "signer", "signature", "certificate", "digest", "hash",
                        "purpose", "invalid", "failed")):
                    clean = re.sub(r"[^a-zA-Z0-9 :=,._()/+-]", "", line)[:160]
                    public_hints.append(clean)
            diagnostic = " public_diagnostic=" + "|".join(public_hints[-12:])[:1200]
        raise AuthenticodeDrillError(
            "upstream cryptographic acceptance predicate failed: phase=" + phase
            + " exit=" + str(completed.returncode) + diagnostic)
    return ok


def make_identity(directory, slug):
    """Build genuine two-level test PKI: root CA and end-entity code signer."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives.serialization import pkcs12
    from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID

    now = datetime.now(timezone.utc)
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    root_name = x509.Name([x509.NameAttribute(
        NameOID.COMMON_NAME, "HamApp CI ephemeral root " + slug)])
    root = (x509.CertificateBuilder()
            .subject_name(root_name).issuer_name(root_name)
            .public_key(ca_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(minutes=5))
            .not_valid_after(now + timedelta(hours=4))
            .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
            .add_extension(x509.KeyUsage(
                digital_signature=False, content_commitment=False,
                key_encipherment=False, data_encipherment=False,
                key_agreement=False, key_cert_sign=True, crl_sign=True,
                encipher_only=False, decipher_only=False), critical=True)
            .add_extension(x509.SubjectKeyIdentifier.from_public_key(
                ca_key.public_key()), critical=False)
            .sign(ca_key, hashes.SHA256()))

    signer_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(
        NameOID.COMMON_NAME, "HamApp disposable Authenticode signer " + slug)])
    leaf = (x509.CertificateBuilder()
            .subject_name(name).issuer_name(root.subject)
            .public_key(signer_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(minutes=5))
            .not_valid_after(now + timedelta(hours=3))
            .add_extension(x509.BasicConstraints(ca=False, path_length=None),
                           critical=True)
            .add_extension(x509.KeyUsage(
                digital_signature=True, content_commitment=False,
                key_encipherment=False, data_encipherment=False,
                key_agreement=False, key_cert_sign=False, crl_sign=False,
                encipher_only=False, decipher_only=False), critical=True)
            .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CODE_SIGNING]),
                           critical=False)
            .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(
                ca_key.public_key()), critical=False)
            .sign(ca_key, hashes.SHA256()))

    password = secrets.token_urlsafe(48)
    pfx = directory / (slug + ".pfx")
    root_pem = directory / (slug + "-root.pem")
    passfile = directory / (slug + ".pass")
    with pfx.open("xb") as stream:
        stream.write(pkcs12.serialize_key_and_certificates(
            b"throwaway-ci-code-signing-leaf", signer_key, leaf, [root],
            serialization.BestAvailableEncryption(password.encode("ascii"))))
    with root_pem.open("xb") as stream:
        stream.write(root.public_bytes(serialization.Encoding.PEM))
    with passfile.open("x", encoding="ascii") as stream:
        stream.write(password + "\n")
    for file in (pfx, root_pem, passfile):
        file.chmod(0o600)
    return {
        "pfx": pfx, "pem": root_pem, "password_file": passfile,
        "fingerprint": hashlib.sha256(leaf.public_bytes(
            serialization.Encoding.DER)).hexdigest(),
    }

def verify(path, identity, expected_success):
    return run([
        "osslsigncode", "verify", "-ignore-cdp", "-ignore-crl",
        "-CAfile", str(identity["pem"]),
        "-require-leaf-hash", "sha2:" + identity["fingerprint"],
        "-in", str(path)
    ], expected_success=expected_success, phase="verify-" + Path(path).stem)


def sign(original, signed, identity):
    run([
        "osslsigncode", "sign",
        "-pkcs12", str(identity["pfx"]),
        "-readpass", str(identity["password_file"]),
        "-h", "sha256",
        "-n", "HamApp CI disposable signature - never distribute",
        "-in", str(original), "-out", str(signed)
    ], phase="sign-" + Path(signed).stem)


def check(unsigned, source_sha, receipt):
    if (os.name != "posix" or os.environ.get("GITHUB_ACTIONS") != "true"
            or os.environ.get("RUNNER_OS") != "Linux"):
        raise AuthenticodeDrillError("isolated GitHub-hosted POSIX cryptographic test only")
    if not SOURCE_SHA.fullmatch(source_sha):
        raise AuthenticodeDrillError("source SHA must be the exact producing commit")
    if unsigned.is_symlink() or not unsigned.is_file() or unsigned.suffix.lower() != ".exe":
        raise AuthenticodeDrillError("actual Windows-built unsigned executable required")
    if receipt.exists() or receipt.is_symlink():
        raise AuthenticodeDrillError("never overwrite acceptance evidence")
    original_sha, original_size = exact_sha256(unsigned)
    runner_temp = Path(os.environ.get("RUNNER_TEMP", "")).resolve(strict=True)
    if runner_temp.is_symlink() or not runner_temp.is_dir():
        raise AuthenticodeDrillError("missing safe hosted runner temporary directory")
    # Never modify original Windows artifact or introduce signing keys into git.
    with tempfile.TemporaryDirectory(prefix="hamapp-authenticode-", dir=runner_temp) as tmp:
        private = Path(tmp)
        private.chmod(0o700)
        first = make_identity(private, "first")
        foreign = make_identity(private, "foreign")
        if first["fingerprint"] == foreign["fingerprint"]:
            raise AuthenticodeDrillError("distinct disposable identities required")
        signed = private / "signed-first.exe"
        wrong_signed = private / "signed-foreign.exe"
        damaged = private / "damaged.exe"
        sign(unsigned, signed, first)
        sign(unsigned, wrong_signed, foreign)
        signed_sha, signed_size = exact_sha256(signed)
        foreign_sha, _ = exact_sha256(wrong_signed)
        if len({signed_sha, foreign_sha, original_sha}) != 3:
            raise AuthenticodeDrillError("real signing did not create unique PE bytes")
        verify(signed, first, expected_success=True)
        verify(wrong_signed, foreign, expected_success=True)
        # Actual negative cryptographic evidence: unsigned input, alien signer
        # against pinned expected cert, mismatched CA and changed signed PE.
        verify(unsigned, first, expected_success=False)
        verify(wrong_signed, first, expected_success=False)
        verify(signed, foreign, expected_success=False)
        shutil.copyfile(signed, damaged)
        with damaged.open("r+b") as stream:
            stream.seek(4096)
            bit = stream.read(1)
            if len(bit) != 1:
                raise AuthenticodeDrillError("built EXE unexpectedly too short")
            stream.seek(4096)
            stream.write(bytes([bit[0] ^ 1]))
            stream.flush()
            os.fsync(stream.fileno())
        verify(damaged, first, expected_success=False)
        # Assert original remains unsigned and byte-identical.
        after_sha, after_size = exact_sha256(unsigned)
        if (after_sha, after_size) != (original_sha, original_size):
            raise AuthenticodeDrillError("input preview was modified during test")
        data = {
            "schema_version": 1,
            "scope": "real-PE-Authenticode-OpenSSL-hosted-disposable-test-only",
            "source_sha": source_sha,
            "unsigned_windows_exe_sha256": original_sha,
            "signed_ephemeral_exe_sha256": signed_sha,
            "real_two_distinct_PE_signatures_cryptographically_verified": True,
            "real_unsigned_executable_signature_rejected": True,
            "real_foreign_signed_publisher_rejected": True,
            "real_wrong_pinned_signer_rejected": True,
            "real_tampered_signed_exe_rejected": True,
            "unsigned_original_unchanged": True,
            "temporary_PFX_and_signed_EXE_deleted_before_artifact": True,
            "windows_native_trust_store_or_OS_WinVerifyTrust_tested": False,
            "real_public_CA_authenticode_certificate_verified": False,
            "owner_production_signature_or_installer_approved": False,
            "public_release_authorized": False,
        }
    receipt.parent.mkdir(parents=True, exist_ok=True)
    with receipt.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, sort_keys=True, indent=2)
        stream.write("\n")
    return data


def main():
    parser = argparse.ArgumentParser(description="Actual offline disposable PE Authenticode acceptance")
    parser.add_argument("--unsigned", required=True, type=Path)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--receipt", required=True, type=Path)
    a = parser.parse_args()
    try:
        check(a.unsigned, a.source_sha, a.receipt)
    except (ValueError, OSError, ImportError, TypeError) as exc:
        parser.exit(1, "REAL_DISPOSABLE_PE_AUTHENTICODE_REJECTED: " + str(exc) + "\n")
    print("REAL_PORTABLE_PE_AUTHENTICODE_CRYPTO_ACCEPTED; NATIVE_WINDOWS_TRUST_AND_PRODUCTION_SIGNER_NOT_VERIFIED")


if __name__ == "__main__":
    main()
