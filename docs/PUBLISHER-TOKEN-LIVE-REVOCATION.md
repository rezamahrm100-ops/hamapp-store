# Private publisher token lifecycle and immediate revocation

Previously the accepted owner-local/HTTPS publisher gateway hashed strong bearer tokens but loaded the registry only when the service started. Revoking a token in the private registry while its service remained running therefore left a **live authorization window**. The owner also had no safe add/rotate/revoke CLI without manually editing the 0600 registry.

## Implemented
- `scripts/publisher_token_lifecycle.py` is **owner-local POSIX CLI only**, not an unauthenticated admin HTTP API. It adds a new source tenant (`add`), replaces its random secret (`rotate`), or invalidates it (`revoke`). It requires an existing 0600 owner-owned credential registry in a 0700 private directory **outside public GitHub source**, never overwrites it with a partial JSON file, uses an exclusive filesystem lock and atomic `os.replace` plus file/directory `fsync`. A new 48-byte random URL-safe token is shown once in the operator's private terminal for add/rotate only; only its SHA-256 digest is persisted.
- The local HTTP and real HTTPS quarantine servers **reopen and validate the private registry on every incoming authenticated upload**, so a rotated/revoked token is rejected on its **next authentication** even if the service has not restarted. If registry is missing, altered, world-readable or malformed, ingress denies with HTTP 503 rather than permitting a stale snapshot. A registry with zero tenants is explicitly valid and **denies all** after revoking the last publisher.
- Original tenant token separation, private exact-byte quarantine, SHA256/size checks, quotas, operator review/approval gates and disabled public distribution remain intact.
- `tests/test_publisher_token_lifecycle.py` uses a **running real local HTTP server** and owner-private disk. It confirms previous bearer works, rotating it rejects the old and accepts the new without a restart, revoked last tenant cannot submit, new tenant cannot impersonate another, changing credential permission/malformed JSON fails closed, and atomic registry/lock permissions are 0600.
- An additional actual HTTPS integration test generates a real temporary OpenSSL X.509 server, connects with validated CA+hostname+leaf pin and demonstrates token rotation/revocation on the **same real TLS server instance**, with no prior or revoked secret accepted.

## Owner-only commands

All paths shown are **private placeholders outside the public source checkout**. A genuine deployment needs an owner-controlled secure host; this source change does not deploy one.

```bash
# Existing credentials were created by the private gateway provision command.
python scripts/publisher_token_lifecycle.py add \
  --registry /secure/hamapp/credentials.json --publisher another-approved-source
python scripts/publisher_token_lifecycle.py rotate \
  --registry /secure/hamapp/credentials.json --publisher another-approved-source
python scripts/publisher_token_lifecycle.py revoke \
  --registry /secure/hamapp/credentials.json --publisher another-approved-source
```

The operator must **securely deliver** a one-time token to the real publisher and revoke it if compromised. This code does not invent that publisher's legal identity. Rotating a token prevents **new** submissions with the old secret, but cannot cancel a request that already authenticated and is in progress. For production add an external verified identity/MFA, admin audit approval, network-side rate limiting, refresh-token policy, encryption/backup/credential management, independently approved first release and operator disaster recovery. A private upload token is never equivalent to publication authorization. No code change enables downloads.
