# HamApp — stable entry point for the next execution

## ACTIVE MISSION OVERRIDE — ONE RUN, FULL TECHNICAL CLOSURE

**Mandatory from 2026-11-02:** The next run is **not** another isolated defect fix or a status report. The primary target is to implement, integrate, test, fix and merge **all technically actionable remaining work across HamApp** in one coordinated execution, to the maximum actually possible. Read the detailed binding contract **[docs/ONE-RUN-TECHNICAL-CLOSURE.md](docs/ONE-RUN-TECHNICAL-CLOSURE.md)** alongside AGENTS.md. This instruction has priority over older entries that suggest stopping after a single feature or one small PR.

Work through Android, Windows, publisher/release/trust pipeline, web/PWA, security, automation, integration and acceptance without requiring another "continue" between safe technical steps. Multiple independently reviewable PRs are allowed inside the same run. Production keys, real owner approvals, physical device consent and administrative controls unavailable through the connector remain explicit external gates; build the safe supporting tooling but do not pretend those gates passed. The final verdict must separate **engineering PASS/PARTIAL**, exact tests and merges, from **production readiness**.


**Canonical detailed task plan:** [docs/NEXT-EXECUTION.md](docs/NEXT-EXECUTION.md). This root file exists so new chats and coding agents can reliably find the handoff. It does not supersede the canonical detailed plan or live GitHub evidence.

## Mandatory order

1. Read [AGENTS.md](AGENTS.md), [docs/ENGINEERING-STATE.md](docs/ENGINEERING-STATE.md), [docs/NEXT-EXECUTION.md](docs/NEXT-EXECUTION.md), [docs/SECURITY.md](docs/SECURITY.md), and [docs/GITHUB-ACCELERATION.md](docs/GITHUB-ACCELERATION.md).
2. Fetch current `main` SHA, recent GitHub workflow runs, open PRs and issues; verify actual acceptance results. Never trust a dated markdown checkpoint as proof.
3. Continue the next complete, **safe** engineering tranche via a reviewable PR. Reuse upstream F-Droid, Android SDK, winget and native GitHub tooling rather than rewriting package managers.
4. Gate changes on hosted Linux/Windows CI, CodeQL and workflow-specific real Android/Windows integration tests. Self-hosted Windows QA is trusted `main` only, never arbitrary PR head.
5. Merge only green/reviewed code and record exact merge SHA, workflow URLs, remaining gaps and next actionable instruction in AGENTS.md / docs/ENGINEERING-STATE.md / docs/NEXT-EXECUTION.md.

## Latest verified engineering milestones (2026-11-02)

- PR #27: actual hosted Android 35 v1→v2 **debug** upgrade and downgrade denial, merged `df47991144c4a226fe76552cadbf351b1bc7c197`.
- PR #28: actual foreign-signer and truncated APK update denial, preserving installed debug v2, merged `1a5e43a4e59d1ce17966c83d6042eb78127fe681`.
- PR #29: offline immutable owner-reviewed web origin/release metadata gate, merged `eb08797a42fdde5cfacd0f6542ee0100d02bb680`. Registries deliberately remain empty. This is NOT a live deployment attestation.

## What is **not** completed

- No independently approved production publisher identities; no stable owner-controlled repo signing key with offline backup; no signed public F-Droid origin and client subscription; no production signed APK/Windows installer; no independent owner-device two-version install/update acceptance.
- No verified eligible private product promoted for public download; no production publisher portal, payments or multi-tenant marketplace. Do not fabricate approvals or convert ephemeral debug keys into trusted production signers.

**Next high-value gate:** independently register a genuine eligible release source, stable developer cert and owner-controlled F-Droid repository signing identity (outside this public repo), verify immutable source/release provenance and a signed production v2 index against an independently pinned fingerprint, then perform F-Droid client install/update and recovery on isolated Android before any public link is enabled.

## One-line instruction for future ChatGPT sessions

> پروژهٔ هَماپ را طبق AGENTS.md و NEXT-EXECUTION.md از آخرین وضعیت واقعی GitHub ادامه بده؛ همهٔ کارهای فنیِ امن و قابل‌اجرا را با GitHub و رانرها در یک ران یکپارچه پیاده‌سازی، آزمون و ادغام کن؛ نتیجه و دستور ادامه را در مخزن ثبت کن.

Repository: https://github.com/rezamahrm100-ops/hamapp-store

## Current integrated branch follow-up (2026-11-02)
Inspect `feature/integrated-technical-closure-20261102` PR, diff, source checks and preview artifacts. Complete/repair and merge only on green checks, then inspect merged main. Continue all remaining engineerable gaps listed in `docs/INTEGRATED-GAP-MATRIX.md` within available tooling; no fabricated release approvals or test keys.

## Offline F-Droid signing custody follow-up
Inspect the actual PR implementing scripts/fdroid_key_custody.py, review its tests/hosted CI, then distinguish working owner-only backup tooling from physically secured persistent owner signing keys and a truly signed published index. Complete all other engineerable gaps in docs/INTEGRATED-GAP-MATRIX.md without waiting for keys.

## Windows installed-state verification follow-up
Check PR `feature/windows-postcondition-verification-20261102` on live GitHub and only merge on successful Linux/Windows CI, CodeQL and hosted native Windows preview. Actual WinGet export readback on the owner's interactive system remains unaccepted until a legitimately approved package exists. Do not confuse this with Authenticode signer validation.

## Real browser acceptance continuation
- Inspect real Chromium PWA acceptance run and artifact from `.github/workflows/pwa-browser-acceptance.yml` before declaring browser UI/offline QA complete. Continue to full a11y/real-device and genuine production identity acceptance after running all feasible source tests.

## Latest authoritative acceptance and next work
Read [docs/ENGINEERING-CLOSURE-2026-11-02.md](docs/ENGINEERING-CLOSURE-2026-11-02.md): PRs #33–#37 were implemented and merged; the latest verified main SHA `8a76c419e581506d395e9eb6e016425d9afa2ca1` passed all six post-merge workflows including actual Chromium offline acceptance, as recorded in the ledger. Do **not** repeat accepted preview/browser work or reinterpret it as production signing.
Continue remaining engineerable backlog (atomic reviewed publisher promotion, real provenance/permission/malware policy, authenticated source workflows, real F-Droid client and Windows release path, mobile/assistive-tech QA) in integrated batches; separate genuine owner-only signing/approvals and branch ruleset (#31). Verdict is PARTIAL until end-to-end scope is demonstrated.

## Current release security engineering batch
Check the latest PR from `feature/secure-release-governance-and-supply-chain-20261102`: real hosted Linux/Windows suite, CodeQL, pinned upstream Trivy source scan and CycloneDX artifact, trusted-main-only owner QA if merged; review safe revocation and proposal-only status. Continue authentic publisher approval, external source/binary malware assessment, F-Droid live signer/index/client and production install paths; do not stop at the PR or claim they were accepted.

## Android real manifest check
- Inspect latest hosted `android-client-preview.yml` run containing actual `aapt dump permissions` and safe receipt. Reject newly requested undeclared permissions and keep public APK approvals disabled. Continue true production key/repo/client install and other engineering gaps.

## Mobile accessibility acceptance gate
Verify exact workflow run for test/mobile-axe-accessibility-20261102: live Chromium axe audit of Persian RTL/mobile dark/light and modal, keyboard navigation, no horizontal overflow. Fix actual issues until green; full assistive-technology and deployment QA remain separate.

## Latest run 2 accepted engineering and next execution
- Inspect `docs/ENGINEERING-CLOSURE-2026-11-02-RUN2.md` and current GitHub before coding. Six PRs #39,#40,#41,#5,#6,#4 merged. Audit exact latest main head and Android F-Droid/emulator hosted checks, then continue authentic publisher/permission/malware/OS signer release integration, owner PR branch ruleset, stable signed index and genuine two-version installs. Do not repeat already accepted Trivy source, aapt or real browser axe QA.

## 2026-11-03 real binary intake batch
Inspect actual PR on branch `feature/actual-binary-archive-inspection-and-owner-intake-20261103` for real hosted Android preview archive receipt, source Linux/Windows tests and CodeQL. Fix failures and merge only after source + actual build pass; then continue secure malware screening of owner-approved actual artifact, genuine signed F-Droid index/client and Windows production signer, and enforce branch review ruleset Issue #31. See `docs/REAL-BINARY-INTAKE.md`.

## First-party live HTTPS deployment control
- Continue from merged repo: inspect PR #44 and real Pages workflow, verify first-party public HTTPS parity on exact main SHA, then pursue genuine third-party signed origin and production publisher/device keys as separate gates. `docs/REAL-PAGES-HTTPS-ACCEPTANCE.md` is authoritative for this check.

## Actual fresh ClamAV artifact scanning
- Review live PR #45 and the actual hosted ClamAV workflow, CI and CodeQL on exact head before merging; check main after. This validates real first-party debug APK signature scanning, not malware absence or any third-party production publisher. Continue offline signer, F-Droid official client, owner device and branch ruleset.

## Latest accepted 2026-11-03 batch — continue unfinished authentic engineering
- Read `docs/ENGINEERING-CLOSURE-2026-11-03.md`; actual merged main `e11f32ae3773e7b5488545230a1e96e27ed8dae4` passed all eight source/debug/binary signature scanner/Windows/Pages workflows. Do not rebuild accepted CRC/ClamAV/HTTPS static tooling. NEXT: genuine owner-approved publisher identity and private submission review; production binary threat/dynamic/legal screening with provenance; admin enforcement of GitHub main branch ruleset Issue #31; stable F-Droid offline production signer/restore and official client two-version install; real Authenticode Windows mapping/update. Continue engineerable code in one integrated execution and keep external owner actions separate. Update this file with exact new SHA and evidence.

## Private publisher quarantine engineering continuation
- Live-check PR from `feature/private-publisher-quarantine-and-review-20261103`, Linux+hosted Windows CI and CodeQL. Accept only with real Linux private disk test coverage and exact main SHA. This adds secure **local** intake / owner crypto handoff; not login, private cloud hosting, tenant authentication or production release. Continue other engineerable gaps, keeping external production identity and branch ruleset (#31) separate.

## Strict F-Droid stage must not bypass owner approval
- Inspect PR for `security/fdroid-stage-requires-real-source-and-malware-preflight-20261103`, actual hosted CI, CodeQL and Trivy. Stage CLI must fail if independently pinned workflow/source ref, permissions or real ClamAV is missing; no unsigned bypass to `fdroid update`. After merging, pursue genuine persistent F-Droid repo signer key/index, official client subscription and two-version signed install, plus Windows production signer and owner-admin branch ruleset (#31). The current public trust registries remain empty.

## Verify signed local F-Droid v2 index and exact APK on real disposable key
- Check branch `security/local-fdroid-signed-v2-index-bound-to-exact-apk-20261103` hosted CI/CodeQL/Trivy plus actual signed-index drill on exact head. Repair real fdroidserver schema/verification discrepancies if present before merge; then inspect main. Owner-independent signer key custody/backup and real HTTPS-origin official F-Droid subscription/install/update remain genuine external gates. See `docs/FDROID-LOCAL-SIGNED-INDEX-ACCEPTANCE.md`.
