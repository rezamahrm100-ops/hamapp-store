# HamApp — engineering state and evidence ledger

Checkpoint: 2026-11-02. Always query live GitHub before trusting this snapshot.

Repository: https://github.com/rezamahrm100-ops/hamapp-store
Default branch: main; public code only, existing proprietary app repositories stay private.

## Last inspected feature commits
- PR #12: https://github.com/rezamahrm100-ops/hamapp-store/pull/12 — merged to main SHA `81effa33d2ace1c537a3de792816cf901d549272`. Release history/revoked certificate/anti-rollback precheck added to F-Droid staging; no live binary published.
- PR #13: https://github.com/rezamahrm100-ops/hamapp-store/pull/13 — merged to main SHA `8ca141f25fed22f053b1d2940ca47e97ebf1ead2`. Public binary downloads require matching approved historical release and pinned publisher. Existing catalogue remains entirely planned.
- PRIOR PR #11: `ba61a72d6383eacbde6310524b82b8ea536a32ca`; agent handoff, CI artifacts and PWA provenance.

## Confirmed check runs on PR #12
- PR CI Linux/Windows: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41479750814 — success.
- PR CodeQL: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41479750912 — success.
- After merge: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41479970518 — owner Windows QA success; plus CI, Pages, PWA evidence and CodeQL successful for that merged SHA.

## Confirmed checks on PR #13 before merge
- PR CI Linux/Windows: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41480594525 — success.
- PR CodeQL: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41480594353 — success.
- Main at `8ca141f2...` started runs:
  - CI: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41480826636
  - Owner Windows QA: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41480826520
  - Pages: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41480826697
  - Static PWA attestation: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41480826823
  - CodeQL: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41480826720
  These run IDs are immutable evidence links, but recheck their terminal status on every continuation.

## Implemented (engineering)
- Persian RTL static PWA with search/platform filters and planned catalogue.
- GitHub Pages, CI hosted Linux/Windows, CodeQL, Dependabot, owner-only trusted main Windows runner, artifact evidence/attestation for static PWA.
- Owner-pinned offline publisher verification via Android apksigner/aapt or Windows Authenticode; failure-closed when registry has no owner-approved signers.
- Offline fdroidserver staging adapter, no deployment/keys.
- `catalog/release_history.json` review-only history schema; pre-publish versionCode/SemVer monotonicity, replay, signer revocation, source/package/signature continuity.
- `scripts/release_review.py` offline plan; no automatic owner approval or publication.
- `scripts/validate_catalog.py` prevents unapproved binary download buttons by cross-checking trusted signer and newest approved history. CI/Pages builds fail on invalid records.
- CODEOWNERS assigns owner review responsibility; it does not enforce branch protection without a configured ruleset.

## NOT accepted: remaining production gates
- Real approved trusted publisher fingerprints (registry empty).
- Actual independent source-to-binary provenance and release signing attestations for each Android/Windows product.
- Persistent offline F-Droid repo signing key, backup, signed published index, trust fingerprint.
- Real signed APK / Authenticode installer validation against independently approved identities.
- Android native branded client, Windows native installer/updater, safe version migration, backend publisher portal.
- Real device install/update between two consecutive signed versions, malformed/rollback/recovery tests.
- Web release verified-deployment origin policy and privacy/permission review.
- Payment/multi-publisher commercial marketplace.
- No real installable package download listed: all entries remain planned.

## Commands for independent confirmation
    gh repo view rezamahrm100-ops/hamapp-store
    gh api repos/rezamahrm100-ops/hamapp-store/commits/main --jq .sha
    gh run list -R rezamahrm100-ops/hamapp-store --limit 20
    gh pr list -R rezamahrm100-ops/hamapp-store
    python -m unittest discover -s tests -v
    python scripts/build_site.py
    python scripts/build_evidence.py --output dist/evidence

## Safety
Self-hosted Windows only on reviewed main; no public PR head code. No secrets/keys in GitHub. GitHub PWA build attestation is not an APK signature. Approved history is user-controlled metadata, not itself cryptographic proof of a release. No fake publisher entries, URLs or signatures.

See NEXT-EXECUTION.md for next integrated work. After every merge record new SHA and complete workflow outcomes.

## New Windows native client preview tranche (2026-11-02)
- Added native Python Tkinter GUI, read-only validated embedded catalogue, bounded winget install/upgrade/show invocation, negative tests, and Windows-hosted PyInstaller build in `.github/workflows/windows-client-preview.yml`.
- All WinGet mappings remain empty: not yet able to install real apps. No signed EXE or owner real desktop UI acceptance.
- **This is an implementation checkpoint, not evidence that GitHub checks succeeded.** Inspect the live PR and action result before accepting.

## Accepted native Windows preview checkpoint (2026-11-02)

- Feature PR #15: https://github.com/rezamahrm100-ops/hamapp-store/pull/15 — merged as main SHA `d420ee6a3a93ec15bad9fec09154c4e5e2f46742`.
- Preview EXE creation on PR branch: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41484276962 — success, artifact `hamapp-windows-unsigned-preview` (short-lived). Hosted Linux/Windows CI: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41484276824 — success; CodeQL: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41484276916 — success.
- After merge to main: hosted CI https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41484700017 — success; owner Windows runner QA https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41484700131 — success; CodeQL https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41484700103 — success; Pages https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41484700659 — success; static PWA evidence https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41484699954 — success; Windows preview EXE workflow https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41484699926 — success, artifact `hamapp-windows-unsigned-preview` observed (expires after 3 days).
- Implemented: native Tkinter Persian GUI; validated offline catalogue snapshot; strict reviewed source-to-winget mapping schema; interactive, fixed-id + source winget install/upgrade/show command construction; no shell injection or silent elevation; PyInstaller preview EXE produced on hosted Windows.
- Not implemented/accepted: code-signed EXE, installer acceptance on interactive owner's PC, independently verified real winget package publisher mapping, actual install/upgrades, persistent signed release, native Android APK client. Production signer registry, release history and winget mapping remain EMPTY; all app install buttons are DISABLED.
- This is a preview engineering milestone, not proof of a production-ready Windows app store or binary-equivalence guarantee.

## In-progress Android native preview (2026-11-02)
- Added native Android Java UI; review-only Android catalogue snapshot generator, F-Droid repo URI validator, runtime signed-repo fingerprint gate and GitHub-hosted Gradle APK build workflow.
- **Unverified until GitHub Android workflow and actual APK artifact complete.** Do not claim signed production build, emulator acceptance, installer operation or real package installation.
- No F-Droid private signing key or approved Android publisher was created. Existing trust registry/history stay empty. Android app cannot install anything in this condition.

## Android emulator smoke check — in progress
- New workflow `.github/workflows/android-emulator-smoke.yml` runs Android 35 x86_64 on GitHub-hosted Ubuntu using the upstream ReactiveCircus emulator runner (Apache 2.0). Installs a Debug APK, launches native UI, checks Arabic-script title and F-Droid button disabled, archives an accessibility dump and screenshot.
- At checkpoint the workflow is **not yet accepted**: inspect actual run's conclusion, artifact and SHA. This is distinct from production signed F-Droid install/update QA.

## Acceptance checkpoint — native Android app and hosted emulator (2026-11-02)

**Implemented and validated:**
- PR #17 https://github.com/rezamahrm100-ops/hamapp-store/pull/17 merged SHA `4688fb18294a1e05ec3f3cf357c6a456a84009fb`.
- Native RTL Java Android UI, offline approved catalogue snapshot generator, strict F-Droid repo fingerprint URI policy, no package install permissions; GitHub-hosted AGP 8.13.0 / Gradle 8.13 debug APK built via upstream tools.
- Hosted debug APK build: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41487326775 — success; artifact `hamapp-android-debug-preview`; ephemeral debug key is not production signer.
- Source PR tests https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41487326902 and CodeQL https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41487326756 — success.
- PR #18 https://github.com/rezamahrm100-ops/hamapp-store/pull/18 merged SHA `56fe430abab33d4c4a843296778ed39c480e860e`. Hosted emulator smoke: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41488084733 — success; Android 35 emulator installed debug APK, launched native UI, found Persian title/planned status and **disabled F-Droid button**, and saved screenshot + accessibility hierarchy artifact `hamapp-android-emulator-evidence`. PR CI and CodeQL passed: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41488084564 and https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41488084433.
- On `main` after PR #18, independently check https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41488539802 (emulator smoke), https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41488540097 (owner Windows), https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41488540082 (CI), https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41488539973 (CodeQL), Pages and build evidence. These might have been running while this documentation was authored.

**Still unaccepted / not done:** Android production APK release key or production signature, a stable independently approved F-Droid repository/index signing key + secure backup, live signed repository subscription/install/update, verified source provenance and publisher registration, any publicly listed genuine Android app, real two-version device installation and rollback, fully embedded F-Droid client fork, and public signed release download. Signer/release/repo registries remain empty; no installation enabled.

**Private-project intake:** authorized GitHub metadata inspection found private Android/Windows projects with some QA/pre-release APK/EXE artifacts. Do not list their identities/contents in this public repository or automatically treat QA builds as approved products. Next must perform independent signer and release readiness verification privately before any publishing.
