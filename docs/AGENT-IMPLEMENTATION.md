# Engineering execution contract for future GitHub-connected agent and owner runner

**Do not claim completed work without a passing run and reviewable SHA.** Current code is V0 storefront. Avoid unrelated work on existing repositories.

## Work order (end-to-end)

1. Read architecture/security docs and inspect actual existing app release repositories and their branch protections and licensing.
2. Implement V1 in a single cohesive PR: manifest v2 with version code, hashes, signer identity; verified import adapter; immutable GitHub release references; signed F-Droid repository with persistent offline key, staging/publication workflow; smoke/negative tests and recovery rehearsal.
3. Implement native Android client via **reused upstream** source, respecting license and signed update path; document independent build/release and verify installation on an actual device.
4. Implement native Windows client or secure Windows package catalogue, choosing an established open package technology where practical; test upgrades and rollback.
5. Implement back-office publishing panel using an established open-source foundation where feasible, protected by GitHub OIDC/short-lived credentials and audit trails.
6. Validate Github CI, CodeQL, Pages, and Windows-owner QA. Use owner runner only when needed, manual dispatch from main, no system-wide modifications without separate approval.

## Non-negotiable acceptance

- Real install/update tests for Android and Windows; SHA256 and signing-certificate continuity checks.
- No secret leakage into public repo, CI logs or artifacts; no unverified public download button.
- Adversarial cases: modified file, wrong signer, old version downgrade, unavailable upstream, revoked access, invalid metadata, API rate limits.
- Build reproducibility, SBOM, docs, fallback/recovery, reviewable immutable release SHA, rollback story.
- Stable RTL, keyboard accessibility, offline behavior, browser smoke tests.
- No manual click-driven local work when an isolated runner can perform it safely; only user-controlled authorizations/OS confirmations remain manual.
