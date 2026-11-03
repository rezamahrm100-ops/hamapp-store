#!/usr/bin/env python3
"""Local publisher uploader: exact-byte, no-token-on-command-line HTTP client.

For owner-controlled POSIX localhost only. It does not grant verified publisher
identity, owner release approval or permission to install/distribute binaries.
"""
import argparse
import base64
import hashlib
import http.client
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

import private_publisher_inbox as inbox
import publisher_intake_service as gateway
import release_integrity


class SubmitError(ValueError):
    pass


def submit(candidate_path, artifact, publisher, token_file, *, port=8765):
    if type(port) is not int or not 1 <= port <= 65535:
        raise SubmitError("invalid localhost port")
    if not isinstance(publisher, str) or not release_integrity.ID.fullmatch(publisher):
        raise SubmitError("invalid publisher source repository")
    token = gateway.private_file(token_file).read_text(encoding="ascii").strip()
    if not 64 <= len(token) <= 128 or any(c.isspace() for c in token):
        raise SubmitError("private token file has an invalid secret")
    metadata_path = Path(candidate_path)
    if metadata_path.is_symlink() or not metadata_path.is_file() or metadata_path.stat().st_size > inbox.MAX_METADATA:
        raise SubmitError("unsafe candidate metadata file")
    raw = metadata_path.read_bytes()
    if not 0 < len(raw) <= inbox.MAX_METADATA:
        raise SubmitError("candidate JSON size out of bounds")
    candidate = json.loads(raw.decode("utf-8"))
    release = inbox.validate_claim(candidate, publisher)
    source = Path(artifact)
    if source.is_symlink() or not source.is_file():
        raise SubmitError("unsafe binary input")
    if source.suffix.lower() != Path(urlsplit(release["asset_url"]).path).suffix.lower():
        raise SubmitError("binary extension mismatch")
    if release["size_bytes"] > gateway.MAX_UPLOAD:
        raise SubmitError("candidate exceeds local gateway upload limit")
    digest = release_integrity.verify_file(release, source)
    encoded = base64.b64encode(raw).decode("ascii")
    if len(encoded) > gateway.MAX_CANDIDATE_HEADER:
        raise SubmitError("candidate cannot fit bounded transport metadata")
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=30)
    try:
        conn.putrequest("POST", "/v1/submissions")
        conn.putheader("Content-Type", "application/octet-stream")
        conn.putheader("Content-Length", str(release["size_bytes"]))
        conn.putheader("X-HamApp-Publisher", publisher)
        conn.putheader("X-HamApp-Candidate-Base64", encoded)
        conn.putheader("Authorization", "Bearer " + token)
        conn.endheaders()
        final_hash = hashlib.sha256()
        remaining = release["size_bytes"]
        with source.open("rb") as stream:
            while remaining:
                part = stream.read(min(1024 * 1024, remaining))
                if not part:
                    raise SubmitError("source truncated during upload")
                conn.send(part)
                final_hash.update(part)
                remaining -= len(part)
            if stream.read(1):
                raise SubmitError("source grew during upload")
        if final_hash.hexdigest() != digest["sha256"]:
            raise SubmitError("binary mutated during upload")
        response = conn.getresponse()
        if response.length is None or response.length > 8192:
            raise SubmitError("unbounded or missing server receipt")
        raw_reply = response.read(8193)
        if len(raw_reply) > 8192:
            raise SubmitError("oversized server reply")
        if response.status != 202:
            raise SubmitError("local quarantine denied upload (HTTP %d)" % response.status)
        data = json.loads(raw_reply.decode("utf-8"))
        if (not isinstance(data, dict)
                or not inbox.ID.fullmatch(str(data.get("submission_id", "")))
                or data.get("status") != "quarantined"
                or data.get("local_token_authenticated") is not True
                or data.get("publisher_identity_independently_verified") is not False
                or data.get("owner_review_approved") is not False
                or data.get("public_distribution_authorized") is not False):
            raise SubmitError("missing required fail-closed server receipt")
        # Recheck the local input after posting; never claim a stable submission if
        # a producer changed source bytes during the operation.
        release_integrity.verify_file(release, source)
        return data
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Send exact private candidate to localhost quarantine only")
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--artifact", required=True, type=Path)
    parser.add_argument("--publisher", required=True)
    parser.add_argument("--token-file", required=True, type=Path)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    try:
        result = submit(args.candidate, args.artifact, args.publisher,
                        args.token_file, port=args.port)
    except (ValueError, OSError, TypeError, UnicodeError, http.client.HTTPException) as exc:
        parser.exit(1, "LOCAL_SUBMISSION_REJECTED: " + str(exc) + "\n")
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    print("QUARANTINED_ONLY; INDEPENDENT_SIGNER_AND_OWNER_APPROVAL_REQUIRED")


if __name__ == "__main__":
    main()
