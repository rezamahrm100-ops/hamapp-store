# Independently reviewed immutable web deployment gate

This is a **static, fail-closed approval metadata gate**, not a cryptographic verification of a live website. It does not fetch a web deployment, inspect redirects, independently verify the asserted source commit, test a browser or prove that bytes delivered by an HTTPS origin match the asserted digest.

## Separate owner-reviewed inputs

- `catalog/trusted_web_origins.json`: schema_version 1; array of app_id, source_repo and canonical HTTPS origin, with no credentials, port, path, query or fragment.
- `catalog/web_release_history.json`: schema_version 1; app_id, source_repo, full lowercase 40-hex source_sha, lowercase 64-hex artifact_sha256, strict SemVer, exact deployment_url, and approved/revoked status.
- `catalog/apps.json`: released web apps must use only the web platform, list a launch URL equal to the independently reviewed latest approved record and a release_proof containing source_repo, source_sha and artifact_sha256.

**Versioned link requirement:** the deployment URL must include `/releases/<40-character-source-commit>/` in its path; a mutable landing page cannot be promoted as a pinned deployment. The exact HTTPS origin, URL and source/digest fields must all match independently registered metadata. A stale, revoked, unknown, spoofed-host or mutable-link release is denied by the catalogue build and hosted CI.

Both owner approval files intentionally start **empty** and must stay empty until a real owner review has independently checked origin ownership, immutable content availability, provenance, artifact integrity, redirects, TLS, app privacy/permissions and deployment rollback. Merely filling in JSON fields is not proof of those facts. GitHub CODEOWNERS identifies review responsibility; enforce repository branch protection/rulesets separately before allowing publisher promotions.

This policy does not authorize publication by itself. It prevents unregistered web launch buttons and keeps all existing planned apps unmodified. Binary Android/Windows gates and the native release signers are separate.

## Local review commands

```bash
python3 -m unittest discover -s tests -v
python3 scripts/build_site.py
```

CI tests synthetic approved records in memory to exercise checks. **No synthetic origin, SHA, digest, approval or download is registered in public files.**

## Future independent acceptance

Require real immutable deployed content and a verified source-to-deployment attestation, an approved owner identity and actual delivered bytes verification; then approve the origin and release-history transaction in a guarded PR. On a security incident revoke the newest record, preventing stale released public URLs. A static gate is not a live runtime integrity monitor.
