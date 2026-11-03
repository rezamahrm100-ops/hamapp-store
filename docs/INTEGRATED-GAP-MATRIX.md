# Integrated technical closure checkpoint — 2026-11-02

This document is a working gap-and-evidence matrix, not a statement that HamApp is complete. Live Actions and the actual merged SHA supersede this snapshot.

| Workstream | Implemented in this tranche | Acceptance | Remaining genuine gaps |
| --- | --- | --- | --- |
| Public PWA/offline | Deterministic planned-only offline snapshot in static build; Service Worker precache and no caching of live release catalogue; fallback UI cannot advertise downloads; JS syntax check | Hosted Linux+Windows CI, static build, negative source tests | Real browser accessibility audit, content/detail/changelog UX, privacy/permission review |
| Windows app operations | Commands run with interactive WinGet in a background thread; return-code is observed; GUI avoids false success or blocking main event loop | Hosted Windows unit tests and unsigned EXE build | Real independently authenticated package mapping, installed-version read-back, signed installer and owner-device install/update |
| Source provenance | Actual `gh attestation verify` invocation pinned to repo/workflow/source-ref/SHA, checks exact local artifact hash and SLSA subject; no injected JSON file is trusted | Synthetic negative control tests + actual gh CLI required when approved real candidate exists | Official owner-approved producer workflow/ref, authentic signed package, real gh verification, malware/permission review |
| Release review | Coordinates existing OS package signature/hash/version continuity and new verified producer attestation; refuses mismatches and never edits catalogue | Unit rejection matrix in CI | Owner-approved PR promotion transaction, real signing keys, approval ruleset and audit |
| Android client | Existing native debug app, F-Droid signed-index drill, v1→v2 update and downgrade/wrong-signer/corruption checks | Previously accepted Android 35 emulator runs | True owner-approved signed index and F-Droid client subscription/install/upgrades with stable repo key |
| Security/automation | Existing CodeQL, artifact attestations, self-hosted trusted-main runner; this tranche adds JS parser checks | Hosted checks | Branch ruleset Issue #31, full SBOM and malware scanner, private source intake |
| Production acceptance | No production trust roots or approved package links are introduced | Fail-closed empty registries | Genuine publisher approval, F-Droid durable offline backup, signed APK/Authenticode, physical-device QA and deployment approvals |
| Multi-publisher/commercial | No change: not a feature completed in this tranche | Not run | Authenticated publisher portal, tenant isolation, moderation, payments and external service readiness |

## Execution discipline

All production signer registries and real web origins remain empty. Synthetic tests confirm **rejection logic** only; source attestations and signature acceptance require real external evidence. No owner desktop or signing material is accessed by PR workflows. The production storefront remains a static demonstrator.

At the next run, first examine the exact integration-branch and main action results, then address the remaining engineering scope in priority order (real Windows installed-state verifier, editor/reviewer promotion pipeline, native Android F-Droid client acceptance, browser/a11y tests, production isolation design). Do not describe this matrix itself as an engineering completion result.

### Durable signer custody extension
Owner-only POSIX external-volume keystore backup/byte parity utility with fail-closed permissions and no secret uploads is in a separate PR (verify merged SHA and CI). **Not** evidence of a real approved signer, disconnected backup, successful restore or production signed index.

### Windows native installed-version continuity extension
The approved WinGet operation path now pre-checks registered version and blocks downgrades/ambiguous versions, then runs a second exact-ID WinGet JSON export to confirm installed version after command exit. Temporary installed-app inventory remains local. Unit tests simulate the official export and check rejection; no owner-approved package mapping or actual install is asserted. Independently verified Authenticode and real interactive system-device acceptance still remain.

### Real browser acceptance extension
A pinned Playwright/Chromium hosted integration test now exercises actual native modal/search/filters and offline service worker behavior with no download controls. Acceptance requires actual workflow run; detailed full screen-reader and mobile browser/accessibility QA is still unaccepted.

## Acceptance reconciliation 2026-11-02
All planned source tranches #33–#37 are now merged and exact feature/main Actions green. Details and remaining full-engineering gaps: [ENGINEERING-CLOSURE-2026-11-02.md](ENGINEERING-CLOSURE-2026-11-02.md). Actual hosted browser test found/fixed insecurely narrow localhost string check; Chromium + offline planned-only controls now accepted. Do not call production signer, publisher platform, real F-Droid client installation, physical device or commercial marketplace accepted. **PARTIAL** engineering closure.

### Candidate promotion, revocation and source supply-chain hardening
New proposed release-governance transaction tooling can generate coordinated no-link revocation patches and owner-review hashes; public source scanned by pinned upstream Trivy + CycloneDX SBOM. **None** of these grant publisher permissions or production malware clearance. After actual CI/Trivy green, remaining tasks include enforced GitHub owner PR approval, real signed APK/EXE scanning/permissions/behavior, persistent F-Droid distribution and authentic installation tests.

### Real Android preview permissions
- New official Android SDK `aapt dump permissions` validation of assembled debug APK and owner-reviewed empty shell permission list. Genuine Android 35 app package validation requires actual hosted run; no application publisher approval, malware sandbox or production signing is implied.

### Mobile browser and automated accessibility
- Hosted real Chromium axe-core WCAG2.1 smoke covers serious/critical rule findings for dark/light/modal on mobile viewport and keyboard dialog navigation. Acceptance depends on exact workflow run; full screen-reader, physical-device and complete WCAG conformance remain external/engineering gaps.

## Second integrated cross-platform implementation: current reference
- See [ENGINEERING-CLOSURE-2026-11-02-RUN2.md](ENGINEERING-CLOSURE-2026-11-02-RUN2.md): actual review-only revoke/release proposals, safe code+SBOM Trivy scan, official Android aapt permissions on real debug APK, mobile axe browser tests with fixed genuine brand-label/contrast issues, compatible official GitHub Pages/checkout upgrades. PRs #39/#40/#41/#5/#6/#4 merged with exact SHAs. **Engineering remains PARTIAL**: approved third-party binary scanning, signer identity, actual paid publisher portal, durable production F-Droid key and client install, signed Windows installer, branch ruleset and physical device acceptance are not fulfilled.

### Actual binary archive integrity and owner-local intake extension (2026-11-03)
- Automated real APK archive entry traversal/CRC/size/ratio inspection and an owner-controlled exact binary signer + signed GitHub producer + Android permission/manifest + final hash check, all fail-closed and review-only. Real Android debug CI artifact required. Still missing genuine approved first-party signer/provenance, dedicated malware and behavioral scan of actual release, full publisher workflow, final approval and real signed F-Droid/Windows device acceptance.

### Real ClamAV artifact signature screening
- Added offline actual candidate ClamAV scan, DB freshness constraint and hash continuity, plus real hosted debug APK scan. This is signature detection only; does not make malware absence claims or fulfill authentic production publisher malware/behavior review.

## Final live 2026-11-03 integration reconciliation
- Latest full evidence ledger `docs/ENGINEERING-CLOSURE-2026-11-03.md` supersedes earlier pending-status sections. Real owner-local upstream signer+GitHub attestation+APK/permission+archive integrity source check accepted as code (no production identity); real first-party debug APK archive and fresh ClamAV signature checks accepted; first-party actual HTTPS Pages delivered-byte parity accepted; main eight workflows all green at `e11f32ae3773e7b5488545230a1e96e27ed8dae4`. Remaining owner/real-product gates include protected PR approval, real malware/dynamic behavior review of approved release, F-Droid production repo/client and Windows Authenticode/owner-device, authenticated multi-publisher management.

### Private publisher intake local queue (2026-11-03)
- Added owner-local POSIX private quarantine file/metadata custody for untrusted publisher submissions, no owner-approval transition, exact byte-hash checks, symlink/duplicate/replay rejection and handoff into actual signed-source/antivirus preflight. This **is not** an authenticated private publisher web portal or an approved commercial marketplace; production auth/tenant quota/storage, signed real packages and admin branch review remain outstanding.

### No-bypass F-Droid staging safety
- Owner-local F-Droid bridge has strict private signer workspace, immutable verified source-to-binary attestation, actual publisher signature, aapt permissions, CRC and ClamAV gates BEFORE upstream index generation, rejecting missing trust evidence. Do not count this as stable production F-Droid signer/index or authorized official F-Droid client subscription. Follow remaining owner-only key and external device gates.

### Local signed F-Droid index bound to approved APK
- Owner-private index-v2 JAR cryptographic signature plus exact package identity/size/hash check added as mandatory `fdroid update` postcondition; failures quarantine private workspace rather than silently accepting/rolling back signed metadata. Requires genuine independent owner key fingerprint and actual hosted signed-index drill success; production public origin/official F-Droid client install remains unmet.

## Actual integrated private-publisher/F-Droid engineering checkpoint, 2026-11-03
- Latest ledger `docs/ENGINEERING-CLOSURE-2026-11-03-RUN4.md`: #47 quarantine actual owner-local app bytes outside repo; #48 source/AV/permissions no-bypass stage gate; #49 actual signed index JAR (upstream fdroidserver) + SHA-bound unique APK version enforced after private `fdroid update`, workspace quarantined on mismatch. PR hosted CI/CodeQL/Trivy + genuine disposable signed-index test passed; main six hosted workflows SUCCESS, owner Windows trusted-main QA #41587826538 QUEUED. Unmet genuine tasks: authenticated production publisher portal/private storage, production approved signer cert and F-Droid key offline backup, signed HTTPS live F-Droid index official client/device install and rollback, production Windows Authenticode, private binary malware/dynamic assessment, enforce GitHub main ruleset Issue #31. Do not declare marketplace production-ready.

## Acceptance update after three 2026-11-03 real integration PRs
- **Closed in source**: first-party owner-local authenticated HTTP upload to private quarantined intake (#51), index-v2 content-consistent two authentic DEBUG APK versions under a stable throwaway repo certificate with verified actual files (#52), disposable F-Droid keystore independently backed up, deliberately deleted and restored before cryptographic re-sign (#53). Real hosted feature acceptance URLs and SHAs: [RUN5 ledger](ENGINEERING-CLOSURE-2026-11-03-RUN5.md).
- **Still an engineering backlog**: remote verified publisher account/tenant/HTTPS upload service (the new port is strictly 127.0.0.1), genuine official F-Droid client install/update test from valid signed test index, full production portal/moderation/privacy, and Windows owner-approved signed-install pipeline. **Real-world owner dependencies**: genuine private source/release + developer signer authorization, stable offline owner key/backup, independent production HTTPS origin/key pin, consented physical-device QA, GitHub protected-main ruleset Issue #31. No production/download claim, even with green CI.

## Current additional closure and remaining gates — 2026-11-03 RUN6
- PR #55: **real** official F-Droid APK and detached GPG crypto/Android developer cert verification, installed APK on isolated Android 35, real explicit `fdroidrepos://` intent to F-Droid, healthy package process; eight feature-hosted checks and eleven merged-main hosted checks PASS. Real third-party UI dump on Android 35 was unavailable, correctly reported FALSE. NOT a genuine repo subscription/app install/update; no trusted public owner repo exists.
- PR #56: candidate real Windows Authenticode two-executable signer and wrong signer/tampering testing; source implemented but **native hosted acceptance pending**, no production signer authorized.
- Still engineerable: official F-Droid client real signed subscription/index refresh/app two-version upgrade, remote verified publisher identity and private HTTPS moderation/storage, production WinGet/installer signing acceptance tooling, malware behavior/privacy/license clearance and device QA. External owner gates: independently approved production certificate/fingerprint, real eligible release, persistent F-Droid key + disconnected backup + HTTPS origin, production install consent, protected-main GitHub ruleset Issue #31. No public download yet.
