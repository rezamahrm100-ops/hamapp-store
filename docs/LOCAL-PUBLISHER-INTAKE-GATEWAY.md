# HamApp owner-local authenticated publisher drop-off (2026-11-03)

## Scope and explicit boundary

`scripts/publisher_intake_service.py` introduces a **real, token-authenticated HTTP upload transport** in front of the already accepted `private_publisher_inbox.py` quarantine. It is deliberately **loopback-only** (`127.0.0.1`). This is not a public HTTPS portal, third-party identity verification, an Internet-facing API, a completed multi-tenant SaaS, or an approval/publishing mechanism.

- A per-source-repository, random 48-byte bearer token is generated once **on the owner's private POSIX host**. Only its SHA-256 is stored in a strictly owner-owned `0600` credentials JSON; the token is displayed once. Do not copy tokens or private credentials into GitHub/Actions/logs/issues.
- The operator controls a private `0700` quarantine and a separate private `0700` temporary upload directory outside the source checkout. The service refuses non-loopback bind, nonprivate modes, symlink credentials and unsafe paths.
- `POST /v1/submissions` takes a bounded raw binary stream with `Content-Length`, `Content-Type: application/octet-stream`, `Authorization: Bearer <local-secret>`, `X-HamApp-Publisher: <source-repo>`, and `X-HamApp-Candidate-Base64: <base64-encoded-original-candidate.json>`. Uploads are limited to 512 MiB, 100 per locally authenticated claimed publisher, and 2 GiB private storage per publisher.
- Before accepting the binary, the service checks token ownership and the complete **untrusted** GitHub release claim; it enforces exact advertised bytes, SHA-256, size, archive structure (for APK/MSIX), and the original local quarantine security controls. It never executes submitted packages.
- A successful HTTP **202** returns only `submission_id`, `status=quarantined`, `local_token_authenticated=true`, with independent developer identity verification, owner approval and public authorization all **false**. It cannot transition a submission to approved.
- The existing owner CLI, fresh antivirus, platform signature, signed upstream provenance and permission checks remain required. Even a valid bearer token cannot satisfy those gates.

## Local-only commissioning (not GitHub-hosted CI)

Use a secure pre-existing owner POSIX directory, separate from this public checkout:

```bash
mkdir -m 700 /secure/hamapp-incoming
python3 scripts/private_publisher_inbox.py init --root /secure/hamapp-private-inbox
python3 scripts/publisher_intake_service.py provision \
  --credential-file /secure/hamapp-private-auth.json --publisher approved-source-repo
python3 scripts/publisher_intake_service.py serve \
  --root /secure/hamapp-private-inbox \
  --temp-dir /secure/hamapp-incoming \
  --credential-file /secure/hamapp-private-auth.json --port 8765
```

The token printed by `provision` is a **private local transport credential**, not a proven GitHub publisher or authority to release. Store it securely. Provision refuses overwrite: to rotate credentials, securely replace the private file under owner control and restart the service. The service does not support public HTTP, proxy forwarding, TLS termination or remote publisher uploads; attaching it to a public proxy would violate its security contract. No unattended distribution starts.

To send a local candidate from an authorized POSIX command environment, encode its exact candidate JSON in the header and POST the raw file with the token. Avoid placing secrets on command lines that may appear in shell histories/process lists; use a secret-aware local client or private process environment. Do not upload owner-held private source, signing keys, or actual releases to public CI.

## Verification and remaining work

The hosted Linux tests use actual loopback HTTP and actual private temporary file copies, while tests use **synthetic bytes only** and no authorized publisher identity. Hosted Windows skips the POSIX-only service by design. Require real PR/main hosted CI, CodeQL and supply-chain checks before accepting source engineering.

Production authentication, MFA, remotely authenticated publisher accounts, audit tamper resistance, TLS ingress, abuse protection, encrypted distributed object storage, trusted package signatures, private malware behavior assessment, owner PR review, persistent F-Droid signing key and official-client release/update QA, Windows Authenticode and real-device consent are **not completed by this work**. Do not infer completed marketplace engineering or enable public links.

## Automated local submission client (no token in CLI arguments)

A matching streaming client, `scripts/local_publisher_submit.py`, performs candidate schema and exact file SHA-256 verification before writing to the local socket, streams the binary without buffering its full size, checks the bounded server receipt and re-hashes the input after transfer. It refuses a nonprivate token file, any external destination or unverified approval claims.

Once the token displayed by `provision` has been placed by the operator in a standalone owner-owned mode-`0600` file outside the public checkout, the supported command is:

```bash
python3 scripts/local_publisher_submit.py \\
  --candidate /secure/source/candidate.json \\
  --artifact /secure/source/candidate.apk \\
  --publisher approved-source-repo \\
  --token-file /secure/hamapp-local-token.txt --port 8765
```

The token must **never** be passed as an argument, stored in public GitHub/CI or printed in request logs. The client returns only the private submission ID and explicit no-release state. An additional owner-only `private_publisher_inbox.py mark --event request_review` plus `owner_candidate_intake.py` cryptographic and antivirus checks are still necessary before a candidate is even eligible for human review; those operations cannot activate publication.
