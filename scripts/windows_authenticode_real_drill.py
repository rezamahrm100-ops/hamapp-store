#!/usr/bin/env python3
"""Test REAL Windows Authenticode on disposable CI certificates, not a release.

The PowerShell caller creates 2 independent temporary code-signing identities,
signs 2 actual Windows preview EXE copies, and passes genuine certificate
fingerprints. This script verifies OS trust, exact binary bytes, publisher
certificate binding and actual denied tampering. No approval/publishing.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

import publisher_gate

class DrillError(ValueError):
    pass

def digest_file(path):
    h = hashlib.sha256()
    size = 0
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
            size += len(block)
    if not 1000 <= size <= 200 * 1024 * 1024:
        raise DrillError("actual Windows preview EXE size out of test bounds")
    return h.hexdigest(), size

def check(unsigned, signed, foreign, intended_certificate, foreign_certificate, source_sha, tamper_path):
    if os.name != "nt":
        raise DrillError("actual Windows cryptographic test only runs on native Windows")
    intended = publisher_gate.normalize_fingerprint(intended_certificate)
    outsider = publisher_gate.normalize_fingerprint(foreign_certificate)
    if intended == outsider or len(source_sha) != 40 or not publisher_gate.COMMIT.fullmatch(source_sha):
        raise DrillError("independent test signers and exact source SHA required")
    unsigned, signed, foreign = (Path(p).resolve(strict=True) for p in (unsigned, signed, foreign))
    if len({unsigned, signed, foreign}) != 3:
        raise DrillError("distinct original and two genuinely signed copies required")
    digest, size = digest_file(signed)
    foreign_digest, foreign_size = digest_file(foreign)
    original_digest, _ = digest_file(unsigned)
    if digest == original_digest or digest == foreign_digest or foreign_digest == original_digest:
        raise DrillError("test binaries were not changed by distinct actual signatures")
    if publisher_gate.verify_authenticode(signed) != intended:
        raise DrillError("real Windows signed EXE publisher certificate mismatch")
    if publisher_gate.verify_authenticode(foreign) != outsider:
        raise DrillError("independently signed foreign EXE certificate mismatch")
    try:
        publisher_gate.verify_authenticode(unsigned)
    except publisher_gate.PublisherError:
        unsigned_refused = True
    else:
        raise DrillError("unsigned preview was accepted")
    release = {
        "app_id": "hamapp-test", "platform": "windows",
        "version": "0.1.0-preview",
        "asset_url": ("https://github.com/rezamahrm100-ops/hamapp-store/"
                      "releases/download/v0.1.0-preview/CI-SYNTHETIC-NOT-PUBLISHED.exe"),
        "sha256": digest, "size_bytes": size,
    }
    candidate = {"release": release, "source_repo": "hamapp-store",
                 "source_sha": source_sha, "package_id": None, "version_code": None}
    registry = {"schema_version": 1, "publishers": [{
        "app_id": "hamapp-test", "source_repo": "hamapp-store",
        "platform": "windows", "certificate_sha256": intended,
        "package_id": None
    }]}
    reviewed = publisher_gate.verify(candidate, registry, signed)
    if (reviewed.get("signer_certificate_sha256") != intended
            or reviewed.get("source_commit_verified") is not False
            or reviewed.get("public_release_authorized") is not False):
        raise DrillError("unexpected source or public release authorization")
    foreign_candidate = json.loads(json.dumps(candidate))
    foreign_candidate["release"].update(sha256=foreign_digest, size_bytes=foreign_size)
    try:
        publisher_gate.verify(foreign_candidate, registry, foreign)
    except publisher_gate.PublisherError:
        foreign_signer_refused = True
    else:
        raise DrillError("real foreign Authenticode signer was accepted")
    target = Path(tamper_path)
    if target.exists() or target.is_symlink() or target == signed:
        raise DrillError("new separate tampered output required")
    shutil.copyfile(signed, target)
    with target.open("r+b") as f:
        f.seek(0)
        f.write(b"XX")
        f.flush()
        os.fsync(f.fileno())
    try:
        publisher_gate.verify(candidate, registry, target)
    except (publisher_gate.PublisherError, ValueError):
        tampered_refused = True
    else:
        raise DrillError("real modified signed EXE was accepted")
    return {
        "schema_version": 1,
        "scope": "isolated-Windows-hosted-ephemeral-Authenticode-real-EXE-signature-drill",
        "source_sha": source_sha,
        "actual_first_party_preview_exe_signed_using_ephemeral_key": True,
        "actual_signed_exe_sha256": digest,
        "real_windows_os_authenticode_signer_verified": True,
        "real_second_foreign_certificate_verified": True,
        "unsigned_original_rejected": unsigned_refused,
        "wrong_real_signer_rejected": foreign_signer_refused,
        "tampered_signed_exe_rejected": tampered_refused,
        "production_authenticode_certificate_verified": False,
        "trusted_prod_publisher_registered": False,
        "windows_real_install_or_upgrade_verified": False,
        "source_provenance_verified_with_owner_approval": False,
        "public_release_authorized": False,
    }

def main():
    p = argparse.ArgumentParser(description="REAL Windows-hosted disposable Authenticode test only")
    for opt in ("unsigned","signed","foreign","tamper-path"):
        p.add_argument("--"+opt, required=True, type=Path)
    p.add_argument("--intended-certificate", required=True)
    p.add_argument("--foreign-certificate", required=True)
    p.add_argument("--source-sha", required=True)
    p.add_argument("--receipt", required=True, type=Path)
    a=p.parse_args()
    try:
        if a.receipt.exists() or a.receipt.is_symlink():
            raise DrillError("receipt must be newly created")
        result=check(a.unsigned,a.signed,a.foreign,a.intended_certificate,
                     a.foreign_certificate,a.source_sha,a.tamper_path)
        a.receipt.parent.mkdir(parents=True,exist_ok=True)
        with a.receipt.open("x",encoding="utf-8") as f:
            json.dump(result,f,sort_keys=True,indent=2)
            f.write("\n")
    except (OSError,ValueError,TypeError,KeyError) as e:
        p.exit(1,"AUTHENTICODE_REAL_EXE_REJECTED: "+str(e)+"\n")
    print("REAL_TEMPORARY_AUTHENTICODE_SIGNATURES_VERIFIED; NO_PRODUCTION_RELEASE")

if __name__=="__main__":
    main()
