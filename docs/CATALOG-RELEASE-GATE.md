# Public catalogue binary download approval gate

Before this gate, a status of `released` with any HTTPS URL could create a download button. Now `scripts/validate_catalog.py` requires a previously owner-approved history entry, a matching independently pinned trusted publisher, exact certificate fingerprint, version, Android versionCode, source repository, signed package ID, SHA-256, file size and a version-qualified GitHub Release URL.

All `released` binary entries must have exactly one platform (Android or Windows) and a `release_proof` object containing exactly: `sha256`, `size_bytes`, `certificate_sha256`, `source_repo`, `package_id`, `version_code`. A revoked signer or revoked newest release blocks download. Newer versions block older listings, preventing accidental rollback.

**Important:** the checkout's approval history is owner-reviewed metadata; this static guard does not itself verify actual binary signatures, Github provenance, malware freedom or file bytes. These belong in the offline publisher verification and signing pipeline. GitHub branch protection/rulesets are needed to enforce reviewed edits to the trust root and catalogue; CODEOWNERS alone does not enforce approval.

Web app listings deliberately remain `planned` until a separate verified web-deployment origin policy is implemented; a random HTTPS URL must not auto-qualify as a verified release.

No app was marked released by this change. All existing entries remain planned and download links remain null.

## CI requirement

Hosted Linux, hosted Windows, CodeQL and trusted-main Windows owner QA must pass. Invalid data must fail the site builder and Pages deployment, preventing unreviewed download buttons. After approval, re-run the source-to-binary and real-device gates before public listing.
