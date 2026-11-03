# Owner-operated HTTPS publisher intake — actual TLS, quarantined bytes, no release

This capability extends the previously accepted loopback-only HTTP gateway, **without weakening the local-only endpoint**. `scripts/remote_publisher_tls_service.py` is a separate dedicated HTTPS-only listener. It reuses the exact prior token authentication, independent hash-and-size comparison, format validation, tenant quotas and POSIX 0700/0600 owner-private quarantine. It **cannot approve, promote, host, install or distribute a package**. Credentials remain owner-controlled outside this public repository.

## What this genuinely implements

- **Real TLS 1.2+ on the listening socket.** Requires an operator-supplied X.509 server certificate + separate private key. The private key must be a regular one-link 0600 POSIX owner-owned file **outside the public checkout**; startup fails otherwise. No plaintext HTTP listener, no TLS downgrade or anonymous/unvalidated upload endpoint. Localhost bind is the safe default; an explicit opt-in is needed before any public-interface bind.
- **Real authenticated publisher transport**, but not independently authenticated *legal developer identity*. The existing registry stores SHA-256 token digests, not plaintext; tenant source names are bound to the token. The remote client `scripts/remote_publisher_submit.py` validates the HTTPS CA trust chain and hostname, then independently pins the exact SHA-256 of the server's presented leaf certificate **before it reads or transmits the publisher bearer token**.
- **Actual binary stream** with maximum Content-Length, SHA-256 and size equality, no symlink/hardlink ingestion, 0700 per-submission folders and 0600 staged files. Per-tenant durable storage quotas remain in the operator's POSIX private queue; no public binary or metadata touches GitHub.
- **Denial and bounded operation.** The dedicated HTTPS server has an 8-connection thread limit, bounded TLS handshake/header timeout, a single active upload slot to avoid concurrent quota races, and 503 retry when busy. No GET review API, no remote PUT/PATCH/DELETE action. Tokens and private candidate file paths never enter access logs. Only a deliberately non-authoritative `202 quarantined` receipt is returned.
- **Reused uploader's exact-byte semantics.** Once CA and server certificate pin succeed, the HTTPS connection is passed to the tested existing `local_publisher_submit.submit`, which revalidates source before/after streaming, refusal envelopes and release-approval flags.

## Isolated real CI tests

`tests/test_remote_publisher_tls_service.py` creates a **real ephemeral local OpenSSL RSA X.509 HTTPS certificate** in a private filesystem directory. It boots a real TLS socket, transmits real test bytes with Python HTTPS and a genuine TLS chain/hostname/SHA-256 pin, verifies actual quarantined file bytes, receipt and private disk permissions, then tests wrong TLS pin, wrong CA, HTTP plaintext downgrade, wrong bearer, cross-publisher claim, private key permissions, non-TLS bind and unauthorized review endpoints. This runs on hosted Linux as part of standard CI. It skips Windows where POSIX mode semantics and OpenSSL are unavailable. This is not a mocked HTTP context and not a fake release approval.

## Operator setup (separate from this public project; no actual deployment performed)

The operator must provision a private POSIX root, a separate private temporary upload directory, a private credential registry and a real TLS certificate with a private key. For example, with all paths outside the source checkout:

```bash
umask 077
mkdir -m 700 /secure/hamapp-publisher /secure/hamapp-publisher/inbox /secure/hamapp-publisher/temp
python scripts/publisher_intake_service.py provision \
  --credential-file /secure/hamapp-publisher/credentials.json \
  --publisher verified-owner-chosen-repository
python scripts/remote_publisher_tls_service.py \
  --root /secure/hamapp-publisher/inbox \
  --temp-dir /secure/hamapp-publisher/temp \
  --credential-file /secure/hamapp-publisher/credentials.json \
  --tls-cert /secure/hamapp-publisher/server.crt \
  --tls-key /secure/hamapp-publisher/server.key \
  --host 127.0.0.1 --port 8766
```

The operator's separate certificate must have the real DNS name in its SAN and a trusted CA chain. A remote publisher would use the **independently communicated** exact TLS leaf SHA-256 pin, trusted CA bundle and its private token-file:

```bash
python scripts/remote_publisher_submit.py \
  --origin https://publisher-api.example.org:443 \
  --trusted-ca-pem /secure/publisher/trusted-server-ca.pem \
  --server-cert-sha256 <independently-reviewed-64-hex-leaf-pin> \
  --candidate /secure/publisher/candidate.json \
  --artifact /secure/publisher/approved-candidate.apk \
  --publisher verified-owner-chosen-repository \
  --token-file /secure/publisher/token.txt
```

The `https://publisher-api.example.org:443` domain is illustrative only: **no DNS, certificate, live public HTTPS endpoint or production server has been deployed or approved**. Public-interface binding would require explicit `--allow-public-bind` and an audited firewall, TLS certificate management, monitoring and abuse limits. In practice prefer an approved TLS proxy with IP-based rate limiting and a private loopback service.

## Explicit unfinished controls

This is a **real working server/client HTTPS transport**, not the full account-backed publisher portal. Verified developer legal identity, MFA, token rotation/revocation/admin invitations, anti-DoS perimeter, external public DNS/certificate/deployment, encryption-at-rest and disaster recovery, human moderation/review/promotion/revocation policy, paid publishing and first approved binary are still needed. No existing token is authorization for public release; on-disk event ledger will continue to mark `publisher_authenticated=false` and `owner_review_approved=false` until independent externally verified controls exist. **Production readiness remains FALSE.**
