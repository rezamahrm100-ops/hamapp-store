# HamApp V1 candidate intake and F-Droid bridge (fail closed)

This is an **offline owner-controlled intake layer**, not an automatic app store installer or public release. Reuses official Android SDK `apksigner` + `aapt`, Windows PowerShell `Get-AuthenticodeSignature`, and upstream `fdroidserver`. No dependencies beyond Python stdlib in HamApp itself. Production F-Droid key material stays outside GitHub and outside this source checkout.

## Trusted publisher registration

`catalog/trusted_signers.json` initially has no registered signers, so **all real candidates are rejected** by default. Before registering a publisher, independently verify ownership, its official GitHub repository, exact Android `package_id` (Windows uses null), and SHA-256 of the actual code-signing certificate. Changes to this registry require owner review; an untrusted PR must never modify the trust root. Existing application private repositories remain private. Record the signer identity from a trustworthy channel (not from a download being reviewed). Never commit private keys.

A registered entry has fields `app_id`, `source_repo` (under `rezamahrm100-ops`), `platform` (`android` or `windows`), `certificate_sha256`, `package_id` (Android package ID or null for Windows). Exact app IDs match approved candidate releases.

## Candidate JSON

Each candidate JSON object contains `release` (the existing six-field `release_integrity.py` manifest), `source_repo`, `source_sha` (40 lowercase hex claimed Git commit ID), `package_id`, and `version_code` (positive Android integer or null for Windows).

## Verify (no network or publishing)

    python scripts/publisher_gate.py --candidate candidate.json --artifact app.apk --receipt verification.json

This checks declared SHA-256, size, HTTPS version-tagged GitHub URL owned by the account, Android APK signature and package/version via SDK tools or Windows Authenticode trust status, and exact pinned signer certificate SHA-256. A passed candidate is a **local evidence receipt**, explicitly `public_release_authorized=false` and `review_required=true`. A source commit SHA value is a *claim*; provenance and build-to-commit matching are NOT verified by this tool. It does not authorize distribution, establish reproducibility, or scan for malware.

Windows verification requires native Windows and PowerShell; Android verification requires independently installed Android SDK tools `apksigner` and `aapt`. Tools that are missing, time out, or return invalid results cause rejection.

## F-Droid owner-controlled staging

Follow upstream official instructions to create a private offline F-Droid workspace with persistent signing key, separate secured backup, and an existing owner-controlled `config.yml`. This workspace must not live in a GitHub checkout or CI artifacts. On POSIX, `config.yml` must have private permissions (`0600` or stricter).

    python scripts/fdroid_bridge.py --candidate candidate.json --artifact app.apk --workspace /path/to/private/fdroid --receipt stage.json

After verifying the same artifact and signer, it copies the APK into the existing workspace and runs **upstream** `fdroid update --create-metadata`. It does not deploy and does not generate a signing key. Before any publication, independently validate the signed index and its fingerprint, audit the APK, review build provenance and permissions, and test install + a two-version update on real devices. Metadata from fdroidserver must never be accepted as permission to replace an existing app signing identity.

## Acceptance boundary

CI uses synthetic/mocked tool output to test *control-flow and rejection*, and never marks a product released. Actual Android SDK signature validation, Windows Authenticode validation of real signed installers, signed F-Droid index generation, secure backup, deployment, and on-device update continuity are **not accepted** until real artifacts, known publisher identities, and owner-controlled signing environment exist.

Upstream instructions: https://f-droid.org/docs/Setup_an_F-Droid_App_Repo/

## Anti-rollback and revocation checks

The F-Droid staging adapter now reads `catalog/release_history.json` and rejects downgrade, replay, revoked signing identities and unexpected signing/source identity changes before staging. To preflight a candidate without running signature tools, call `python scripts/release_history.py --candidate candidate.json`. To verify actual file bytes plus APK or Windows signature and produce a review-only receipt, use `python scripts/release_review.py --candidate candidate.json --artifact package.apk --receipt review.json`. These controls never append approval records or publish binaries. History/registry edits require owner review. See [RELEASE-HISTORY.md](RELEASE-HISTORY.md).
