#!/usr/bin/env python3
"""Generate TWO independent disposable CodeSigning PFX identities on hosted Windows.

Uses upstream pyca/cryptography/OpenSSL software keygen to avoid a stalled
Windows CNG self-signed key provider. Credentials NEVER leave RUNNER_TEMP,
are never printed, uploaded, put in public registry, or valid for production.
"""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets

class EphemeralSignerError(ValueError):
    pass

def generate(directory):
    if os.name != "nt" or os.environ.get("GITHUB_ACTIONS") != "true" or os.environ.get("RUNNER_OS") != "Windows":
        raise EphemeralSignerError("GitHub-hosted Windows cryptographic test only")
    base = Path(directory)
    if base.exists() or base.is_symlink() or not os.environ.get("RUNNER_TEMP"):
        raise EphemeralSignerError("new temp-only signer directory required")
    parent = Path(os.environ["RUNNER_TEMP"]).resolve(strict=True)
    if base.resolve().parent != parent:
        raise EphemeralSignerError("disposable identities must stay directly in runner temp")
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives.serialization import pkcs12
    from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID

    base.mkdir(mode=0o700)
    result = {}
    for keyname in ("a", "b"):
        # A CA used as an Authenticode *leaf* can be rejected by native
        # WinVerifyTrust. Build two independent CA->non-CA code-signing leaves
        # entirely in short-lived hosted-memory/runner-private temp.
        now = datetime.now(timezone.utc)
        ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        signer_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        ca_name = x509.Name([x509.NameAttribute(
            NameOID.COMMON_NAME, f"HamApp Disposable CI Root {keyname.upper()} NEVER PRODUCTION")])
        leaf_name = x509.Name([x509.NameAttribute(
            NameOID.COMMON_NAME, f"HamApp Disposable CI Code Signer {keyname.upper()} NEVER PRODUCTION")])
        ca = (x509.CertificateBuilder()
              .subject_name(ca_name).issuer_name(ca_name).public_key(ca_key.public_key())
              .serial_number(x509.random_serial_number())
              .not_valid_before(now-timedelta(minutes=5))
              .not_valid_after(now+timedelta(hours=4))
              .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
              .add_extension(x509.KeyUsage(
                  digital_signature=False, content_commitment=False,
                  key_encipherment=False, data_encipherment=False,
                  key_agreement=False, key_cert_sign=True, crl_sign=True,
                  encipher_only=False, decipher_only=False), critical=True)
              .sign(ca_key, hashes.SHA256()))
        leaf = (x509.CertificateBuilder()
                .subject_name(leaf_name).issuer_name(ca.subject)
                .public_key(signer_key.public_key())
                .serial_number(x509.random_serial_number())
                .not_valid_before(now-timedelta(minutes=5))
                .not_valid_after(now+timedelta(hours=3))
                .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
                .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CODE_SIGNING]),
                               critical=True)
                .add_extension(x509.KeyUsage(
                    digital_signature=True, content_commitment=False,
                    key_encipherment=False, data_encipherment=False,
                    key_agreement=False, key_cert_sign=False, crl_sign=False,
                    encipher_only=False, decipher_only=False), critical=True)
                .sign(ca_key, hashes.SHA256()))
        password = secrets.token_urlsafe(32)
        pfx_path = base / (keyname + ".pfx")
        cer_path = base / (keyname + ".cer")
        root_path = base / (keyname + ".root.cer")
        with pfx_path.open("xb") as stream:
            stream.write(pkcs12.serialize_key_and_certificates(
                b"HamApp-Disposable-Code-Signer-TEST",
                signer_key, leaf, [ca],
                serialization.BestAvailableEncryption(password.encode("ascii"))))
        with cer_path.open("xb") as stream:
            stream.write(leaf.public_bytes(serialization.Encoding.DER))
        with root_path.open("xb") as stream:
            stream.write(ca.public_bytes(serialization.Encoding.DER))
        result[keyname] = {
            "pfx": str(pfx_path),
            "cer": str(cer_path),
            "root_cer": str(root_path),
            "password": password,
            "certificate_sha256": hashlib.sha256(
                leaf.public_bytes(serialization.Encoding.DER)).hexdigest(),
        }
    with (base/"private-material.json").open("x", encoding="utf-8") as f:
        json.dump(result, f)
    print("TWO_DISPOSABLE_OPENSSL_PFX_GENERATED_ONLY_IN_HOSTED_TEMP; NOT_PRODUCTION")

def main():
    p=argparse.ArgumentParser(description="One-run hosted Windows CI disposable cryptography test")
    p.add_argument("--directory",type=Path,required=True)
    a=p.parse_args()
    try:
        generate(a.directory)
    except (OSError,ValueError,ImportError,TypeError) as e:
        p.exit(1,"DISPOSABLE_WINDOWS_TEST_SIGNER_FAILED: "+str(e)+"\n")

if __name__=="__main__":
    main()
