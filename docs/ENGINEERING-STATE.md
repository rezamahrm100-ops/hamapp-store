# HamApp — engineering state and evidence ledger

## Effective next-run objective (2026-11-02): integrated engineering closure

The project owner has replaced the incremental microfix/status-report mission with **one coordinated effort to close every technically actionable workstream**. The mandatory contract is [docs/ONE-RUN-TECHNICAL-CLOSURE.md](ONE-RUN-TECHNICAL-CLOSURE.md); root AGENTS.md and both NEXT-EXECUTION.md files link to it. Agents must inventory gaps, execute implementation and real checks across Android/Windows/PWA/publisher/security/release pipelines, integrate reviewable PRs where possible, and record a strict PASS/PARTIAL engineering verdict.

This policy **does not mark any remaining feature as implemented** and **does not authorize invented signatures, persistent production keys in public CI, private project publication or unattended owner-device changes**. Real owner/external prerequisites remain explicit blockers after the corresponding technical tooling is completed.


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

## Native binary build provenance checkpoint (2026-11-02)
- Added first-party actions/attest@v4 for Android debug APK and unsigned Windows EXE, followed by independent gh attestation verify pinned to actual producing workflow, main ref, full source SHA and hosted runner. Review-only digest receipt is generated and short-lived.
- This is NOT proof of run success until inspected after main merge: verify actual build, attestation, independent verification and receipt artifacts on both workflows. No production signed release or real app download is authorized.

## Accepted native GitHub build provenance (2026-11-02)
- PR #20 merged main SHA 5429ee5d259b138c7478a5c15b226c4b995c1d5b.
- Android debug APK build + signed provenance + independent gh CLI verification: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41491331966 — success, artifact hamapp-android-debug-provenance.
- Windows unsigned EXE build + signed provenance + independent gh CLI verification: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41491331958 — success, artifact hamapp-windows-unsigned-provenance.
- Additional main checks: CI https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41491331877; CodeQL https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41491331997; trusted owner Windows QA https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41491331983; Pages https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41491331975 — all success.
- These attest only GitHub build provenance. Android APK remains debug-signed; Windows EXE unsigned; no approved publisher/repository identities or production installs.
- New fdroidserver signed-index v2 checker requires independently approved URL/fingerprint; its unit tests use injected synthetic responses. **Do not mistake green CI for live signed-index acceptance**. No production index is configured.

## Final acceptance of 2026-11-02 build provenance and F-Droid preflight
- PR #20 merged SHA 5429ee5d259b138c7478a5c15b226c4b995c1d5b. Real Android debug APK attestation and cryptographic gh attestation verify: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41491331966 (success; provenance receipt artifact). Real unsigned Windows EXE attestation/gh verify: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41491331958 (success; receipt). Main CI https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41491331877, CodeQL https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41491331997 and owner Windows QA https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41491331983 also success.
- PR #21 merged SHA 0da534fd3e658ed2398a031b71da43043e76a4df. New fdroidserver.index.download_repo_index_v2 preflight rejects missing/unpinned URL or fingerprint and never falls back to unverified metadata. Negative/contract tests use mock upstream response; **not a live F-Droid index signature verification**. CI https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41492388988, CodeQL https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41492389009, owner Windows https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41492389209, Pages https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41492389297 and PWA evidence https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41492389233 all success.
- Remaining absolute production blockers: owner-reviewed release key and developer certificate identities, persistent F-Droid repo key plus independent offline backup, signed v2 index actually deployed, first approved app with verified build-origin/OS signature, Android real two-version install/update, signed Windows EXE and real install/update. Download and install controls remain disabled.

## In-progress real signed-index F-Droid integration drill
- PR introduces hosted-main Ubuntu workflow with actual fdroidserver init/update on HamApp Android debug APK, local-only HTTP signed index-v2 verification, tampered-index and wrong-fingerprint rejection. Uses disposable signing key, never production key, no deployment or installation.
- Status NOT ACCEPTED until actual GitHub run succeeds and review-only receipt artifact is confirmed. Official library integration is tested in the workflow, separate from mocked preflight unit tests. No production repository is configured.

## In-progress two-debug-version Android emulator upgrade (2026-11-02)
- New hosted GitHub Actions smoke tests real Android 35 install versionCode=1, upgrade versionCode=2 with same temporary debug signer, default downgrade refusal and native safe UI after upgrade. Requires actual run success + evidence artifact for acceptance.
- No real publisher-approved app, signed F-Droid client subscription, stable production release signing or owner-device update acceptance. See docs/ANDROID-TWO-VERSION-SMOKE.md.

## Android negative-install acceptance extension (implementation, not yet accepted)
- Branch `feature/android-package-rejection-qa-20261102` adds wrong-signer APK and deliberately truncated APK rejection on real hosted Android 35 emulator after successful v1→v2 debug upgrade and default downgrade refusal. It verifies v2 remains installed after each denied update and does not upload test keys/APKs.
- **Do not call accepted until the actual branch CI, CodeQL, and emulator run all succeed and are inspected.** Neither this test nor the previous ephemeral signed-index drill is production signing or real owner-device acceptance.


## 2026-11-02 unified acceptance ledger — PRs #27, #28 and #29
- **Android upgrade acceptance**: PR #27 merged as `df47991144c4a226fe76552cadbf351b1bc7c197`; real hosted Android 35 debug v1→v2 installation/upgrade, default downgrade rejection, safe Persian UI and artifact. PR emulator https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41498803142; merged main emulator https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41504126166 — SUCCESS.
- **Android negative-package acceptance**: PR #28 merged as `1a5e43a4e59d1ce17966c83d6042eb78127fe681`; real hosted Android emulator denies a separately re-signed APK and truncated APK, preserving v2. PR emulator https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41504576824 (SUCCESS, artifact `hamapp-android-debug-two-version-upgrade-evidence`); PR CI https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41504576692 and CodeQL https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41504576810 — SUCCESS. On merged main: CI https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41505157829, owner Windows https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41505157704, CodeQL https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41505158010 and Android emulator https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41505157772 — SUCCESS.
- **Immutable web launch gating**: PR #29 merged as `eb08797a42fdde5cfacd0f6542ee0100d02bb680`; requires separately registered HTTPS origin and newest owner-reviewed SHA-versioned web deployment record before a web release launch button passes static catalogue CI. PR CI https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41505384878; CodeQL https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41505384980; hosted Windows EXE https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41505385179; hosted Android APK https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41505384967 — all SUCCESS. Main SHA latest at this checkpoint `eb08797a42fdde5cfacd0f6542ee0100d02bb680` had successful CI https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41505611808 and PWA build evidence https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41505612012; other main workflows were still running and MUST be checked at continuation.
- Previous actual signed F-Droid v2 disposable-index drill on main SHA `41e7b852dce83259f0cff7044b261a20b177f07b`: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41497810315 — SUCCESS, safe evidence artifact `hamapp-ephemeral-fdroid-signed-index-evidence`. This is upstream fdroidserver validation under **ephemeral CI signing**, not persistent production trust.
- All public registries for publisher, F-Droid repo and web origin remain empty/null; no production signing keys, approved real releases, production download links, real owner-device updates, public signed index or true F-Droid client subscription. The source code guards are valuable but are not the missing genuine identities and independent acceptance.
- Stable next-chat entry point: root `NEXT-EXECUTION.md` -> `docs/NEXT-EXECUTION.md`. Read root AGENTS.md and always inspect actual live GitHub before changing any acceptance status.


### Final live recheck of PR #29 merged main
All seven main checks for `eb08797a42fdde5cfacd0f6542ee0100d02bb680` now completed **SUCCESS**: CI https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41505611808; CodeQL https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41505612155; owner Windows QA https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41505612176; Android preview https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41505612008; Windows EXE preview https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41505612132; Pages https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41505611948; reproducible PWA evidence https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41505612012. These are validated source/debug/unsigned preview checks, NOT real production publisher release acceptance.

## Integrated PWA/Windows/provenance code tranche — verification pending
- Feature branch `feature/integrated-technical-closure-20261102` implements a planned-only PWA offline snapshot and live catalogue non-cache policy; WinGet background execution with exit-code reporting (not actual installed-version readback); actual GitHub signed provenance verifier; and a combined OS signature + attestation review-only gate.
- This is a **code implementation checkpoint only** until actual hosted checks succeed and branch merges. Synthetic unit receipts never authorize publication. See `docs/INTEGRATED-GAP-MATRIX.md` for full remaining work; owner signers/repos/approvals remain unregistered.

## Isolated F-Droid key-custody tooling (implementation pending real CI)
- Proposed offline owner-only command creates and verifies a no-overwrite 0600 keystore backup on a separate mounted filesystem, refuses symlinks/checkout paths, and does not expose material to public GitHub. POSIX dummy fixture tests do NOT prove real owner keys are backed up, physically offline or restorable. Check actual PR workflow and merge SHA.

## Windows package installed-state gate (implementation awaiting CI)
- New independent WinGet export JSON readback checks exact approved package ID and installed version before/after interactive WinGet; rejects downgrades, ambiguity and mismatch; user-visible UI no longer equates exit=0 to installed package confirmation. Source tests use synthetic Windows package inventory. No actual approved software has been installed, no Authenticode production signer is registered, and no owner desktop changes were attempted.

## Real Chromium PWA acceptance implementation (CI pending)
- New independent hosted workflow runs a genuine headless Chromium against validated built site, tests app detail interactions, search/filter, service-worker offline reload and that offline mode cannot advertise unapproved downloads. An actual successful run/screenshot is required before claiming acceptance; browser/device/signed production release remain unverified.

## Accepted integrated 2026-11-02 engineering sequence and final merge
Read [ENGINEERING-CLOSURE-2026-11-02.md](ENGINEERING-CLOSURE-2026-11-02.md) for immutable PR #33–#37 SHAs, all successful feature workflows and explicit outstanding gaps. Final feature PR #37 merged `8a76c419e581506d395e9eb6e016425d9afa2ca1`. Source CI https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41513411248 ; CodeQL https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41513410815 ; trusted-main Windows https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41513410898 ; Pages https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41513410791 ; PWA evidence https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41513410837 ; **real Chromium offline acceptance** https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41513410860 — all completed SUCCESS on this exact SHA. No claim of genuine production app, live F-Droid repository signing or physical owner-device installs. **Engineering PARTIAL; production NOT accepted**.

## Release governance + upstream source security integration (implementation, acceptance pending)
- Implemented proposal-only atomic release and signer revocation with safe unpublishing/revocation state and canonical before/after hash audit; no direct repo writes. Fixes per-app **platform-specific** independent signer registration. Adds real upstream pinned Trivy hosted public-source vulnerability/secret/config scan and a CycloneDX source SBOM. Tests synthetic release records only. Status NOT accepted until actual hosted CI/CodeQL/Trivy workflow results and post-merge checks inspected. Production source/artifact malware, publisher approval, branch ruleset and live F-Droid/Windows device acceptance remain unsatisfied.

## Android real APK manifest permission gate (pending PR acceptance)
- A GitHub-hosted APK build workflow now invokes official Android SDK `aapt` on actual debug APK bytes; validates exact package/version and a fail-closed reviewed permissions allowlist. Uploads a safe short-lived digest/permissions-only receipt, not a key. Source tests mock aapt only and are not sufficient to claim real acceptance; check actual Android preview workflow after merge. This does NOT establish production malware or developer signer identity.

## Hosted mobile Chromium accessibility gate (implementation, acceptance pending)
- New actual 390x844 Chromium mobile context with pinned axe tests for A/AA serious/critical, dark/light/native-dialog modes, keyboard Escape and horizontal overflow; NOT full WCAG certification. Check real PR and main workflow acceptance before marking success.

## Second integrated engineering execution: accepted merges and live QA reconciliation
- Six PRs #39/#40/#41/#5/#6/#4 merged. Source of exact SHAs, feature-branch CI/CodeQL/Trivy/Android aapt/Chromium axe and Pages evidence: `docs/ENGINEERING-CLOSURE-2026-11-02-RUN2.md`. Main checkout-v7 merge `86b47e7839c4c63f722da448ebdee1f3fcda163c` requires exact terminal confirmation of 12 workflows; do not interpret pending as pass. Actual owner Windows runner 2.338.2 is above upstream checkout Node24 requirement 2.327.1. Public signers, release history, F-Droid repository and trusted web origins still empty/null; production readiness rejected.
