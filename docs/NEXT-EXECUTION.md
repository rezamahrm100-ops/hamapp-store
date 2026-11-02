# HamApp — next coherent engineering batch

Mission: convert verified catalog + candidate intake into a safe real publishing pipeline, then native clients, without requiring repetitive owner commands. If no trusted real app binary, complete all synthetic/offline engineering and report exact missing real-world evidence rather than making fake packages.

## Workstream A — publisher/release engineering
1. Enumerate target owned repositories and public release endpoints using authorized GitHub connector. Keep their private source private; select only actual builds.
2. Resolve exact release signing certificate fingerprints from a trusted owner-controlled source; never trust fingerprints provided by the very file being evaluated. If no approved signer, preserve fail-closed empty registry.
3. Add immutable source build attestations for newly built Android/Windows artifacts in their producing repositories, not just HamApp; match SHA, versionCode and cert continuity.
4. Implement registry schema v2, stable update history, stale/revoked key handling, rollback protections, atomic publishing and strict tests. No public download until independent checks.
5. Package signed F-Droid index using upstream fdroidserver in isolated trusted signer environment; preserve persistent key and separate backup. Verify official client subscription and two-version update on an approved device.

## Workstream B — installer clients
1. Evaluate maintained upstream F-Droid Android client at pinned revision, license/compliance and Android target requirements. Prototype branded UI by adapting upstream, not reinventing APK installer.
2. Use winget/MSIX/AppInstaller identities for Windows wherever feasible; build a verified manifest, installer interaction, update/rollback and cross-platform contract tests.
3. Use hosted CI and isolated Android/Windows test devices; preserve owner runner for trusted main Windows-only QA.

## Workstream C — publisher portal and catalog
1. Choose backend only after real authentication need; start with GitHub PR-based publishing review and structured release evidence.
2. Implement app detail pages, screenshots, changelog, categories and safe approved downloads; no invented numbers/stars.
3. Add staged rollout, revoke/rollback, availability checks and privacy-conscious audit trail.

## Workstream D — quality and delivery
1. All new feature PRs: Linux CI, hosted Windows, CodeQL, negative security tests, provenance evidence. Owner Windows runner runs trusted main after merge.
2. Use SBOM/provenance for real build outputs and keep production signing offline; publish validated release assets via immutable tags.
3. Maintain root AGENTS.md and docs/ENGINEERING-STATE.md with real run links/SHA, blockers, next batch.
4. Finish when each user-facing capability passes real installation/update/security tests, not merely when scripts exist.

## No-dead-end operator policy
- Prefer one integrated implementation tranche over repeated small requests.
- Take permitted action in GitHub and use available hosted/self-hosted runners; do not ask user to click through steps for technical work you can do directly.
- No automatic escalation of GitHub App scopes or use of unknown credentials.
- If owner approval/OS UAC/key creation/actual device access is unavoidable, isolate it as a single precise acceptance gate; continue all independent engineering in parallel.
- Explicitly distinguish complete implementation, green hosted CI, owner-runner acceptance, real-device QA and public commercial readiness.

## After release-continuity PR is accepted
- Inspect owner-reviewed `catalog/release_history.json` and test promotion/revocation against real signed artifacts, not mock fixtures.
- Set a protected workflow for promoting authenticated publisher releases with independent provenance and signer continuity; no implicit trust from a PR-provided manifest.
- Implement Android native client upstream reuse and native Windows updater in separate coherent workstreams; use existing package-manager APIs.
- Keep user-action gates limited to genuine signing/owner/device authorizations; never infer an installed product from green CI.

## After catalogue approval gate
- Integrate cryptographic GitHub build-attestation VERIFICATION at the producing app repositories, not just a claimed commit ID in JSON.
- Introduce real, separately trusted web-deployment origin approval to enable web app listings (the binary-only gate deliberately refuses web downloads).
- Create operator-controlled, auditable promotion workflow for actual approved releases after binary signature, malware, two-version update and provenance checks. Do not accept a forged receipt supplied in a PR.
