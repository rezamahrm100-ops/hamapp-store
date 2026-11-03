# HamApp — canonical agent handoff

## PRIMARY EXECUTION DIRECTIVE — full technical closure, not another microfix (effective 2026-11-02)

**The next engineering run MUST target end-to-end closure of all technically actionable HamApp workstreams in one integrated execution.** Do not treat a one-defect PR, a scan of current status, or a planning-only response as completion. Read **[docs/ONE-RUN-TECHNICAL-CLOSURE.md](docs/ONE-RUN-TECHNICAL-CLOSURE.md)** before doing anything beyond verifying live GitHub. It is the controlling mission and acceptance contract; keep existing safety, private-key custody, review and trusted-main-only runner limits.

Cover Android, Windows, web/PWA, publisher/release workflow, security, distribution tooling, integrations and real automated acceptance together. Implement and merge separately reviewable PRs within the same execution instead of pausing between small stages. Use GitHub Free, hosted checks, authorized trusted-main owner Windows QA, pinned open-source tools and existing code. Finish as much as the actual tools/permissions allow; fix failed tests and re-run, verify real main SHAs. **Do not fabricate production signing, publisher approval, public binaries or device tests.** Isolate unavoidable owner/real-world gates, leaving their engineering tooling complete.


**Read this file first in every new chat, coding-agent session or runner task.**

Repository: https://github.com/rezamahrm100-ops/hamapp-store
Website (public static demo): https://rezamahrm100-ops.github.io/hamapp-store/
Owner: rezamahrm100-ops
Default branch: main

## What exists
- Persian RTL installable PWA catalogue (web/index.html, web/app.js, web/styles.css, catalog/apps.json).
- Python-stdlib site builder, catalogue validation and tests.
- Offline hash/size candidate gate (scripts/release_integrity.py).
- Offline publisher/signature gate and F-Droid staging bridge (scripts/publisher_gate.py, scripts/fdroid_bridge.py).
- GitHub-hosted Linux/Windows CI, CodeQL, Dependabot, Pages, and a separately registered owner Windows runner (hamapp-windows).
- Release evidence workflow and reproducible PWA ZIP (after this change is merged).

## Not completed / not authorized to claim
- No approved Android/Windows publisher identities: catalog/trusted_signers.json is empty.
- No real signed production F-Droid repository or offline key backup.
- No branded native Android client or Windows installer/updater.
- No independent two-version real-device install/update acceptance.
- No multi-publisher portal, paid marketplace or production account service.
- All public catalogue entries are planned; none have an approved download link.
- A green CI or an attested PWA ZIP does NOT mean a signed app or live marketplace.

## Read before making changes
1. docs/ENGINEERING-STATE.md (status + precise verification commands).
2. docs/GITHUB-ACCELERATION.md (existing/free tooling and cost/security limits).
3. docs/OPEN-SOURCE-REUSE.md (upstream reuse / licensing decisions).
4. docs/NEXT-EXECUTION.md (one coherent next engineering batch).
5. docs/SECURITY.md, docs/PUBLISHER-PIPELINE.md, docs/ROADMAP.md.

## Fast execution contract
- Inspect live main SHA, open PRs and latest check runs from GitHub. Documents are handoff context, NOT proof of today's runtime status.
- Prefer existing mature open-source tools, fork or vendor only when licensing/security and maintenance permit; pin versions and provenance.
- Implement one cohesive PR per independent tranche; run Linux + hosted Windows + CodeQL, investigate failures, then merge only green/reviewed code.
- User explicitly prefers GitHub/runner automation and no piecemeal local UI work. Do not request manual steps for tasks executable with authorized connectors and runners.
- Self-hosted Windows runner is for owner-trusted main only. Never run PR head, untrusted contributors, downloaded arbitrary code, or private secrets through public PR workflows.
- No owner signing keys in GitHub; no private source or user data copied into this public repository.
- Use immutable release identifiers, signer continuity, SHA256 and version-code checks; never turn on download links from synthetic fixtures.
- Never claim a change, workflow run, merge, installation or release succeeded without a real SHA/run URL/evidence.
- Keep this file and ENGINEERING-STATE.md updated when architecture or acceptance status changes.

## Local commands
    python -m unittest discover -s tests -v
    python scripts/build_site.py
    python scripts/build_evidence.py --output dist/evidence

Windows owner QA: .github/workflows/windows-qa.yml (main-only); ordinary CI: .github/workflows/ci.yml.
For a new chat: "Open AGENTS.md and docs/NEXT-EXECUTION.md at the current main SHA, inspect live checks, then continue the entire safe engineering batch via PR."

## Release continuity policy (added 2026-11-02)
- Read docs/RELEASE-HISTORY.md before release work. New release_history.py and release_review.py provide fail-closed pre-publish rollback/replay/revocation checks, not production authorization.
- catalog/release_history.json is initially empty; do not fabricate approved history or signer fingerprints. F-Droid offline staging now checks this ledger before accepting candidates.

## Public download admission rule
- Before enabling `released` in public catalog/apps.json read docs/CATALOG-RELEASE-GATE.md. HTTPS alone is NEVER evidence of signed software. Production binary listings must match approved history and independently registered publisher, while actual signing/provenance/device gates are separate.

## Accepted V1 release metadata hardening
- See docs/RELEASE-HISTORY.md and docs/CATALOG-RELEASE-GATE.md: review-only historical anti-rollback checks and approved-download gating. Historical PRs #12 and #13 merged 2026-11-02; their exact verified workflow evidence and outstanding gaps live in docs/ENGINEERING-STATE.md.
- Never mistake this for completed production F-Droid signing or native Android/Windows clients.

## Native Windows desktop preview (2026-11-02 implementation)
- Read docs/WINDOWS-CLIENT.md. The project includes a Python Tkinter/official winget client with owner-curated mapping, strict version/package IDs, explicit user confirmation and hosted Windows PyInstaller build.
- It is **unsigned**, not production release. All package mappings are empty, so no app installs are enabled. Check actual Windows preview workflow result before claiming EXE created.
- No unattended WinGet actions on the owner runner; client UI and signing identity require separate real-device and owner approval.

## Native Windows preview accepted (2026-11-02)
- PR #15 on main `d420ee6a3a93ec15bad9fec09154c4e5e2f46742`: actual GitHub-hosted Windows PyInstaller unsigned preview EXE built, Linux+Windows CI, CodeQL, self-hosted owner Windows QA, Pages and PWA evidence all passed. See docs/ENGINEERING-STATE.md for immutable run links.
- Read docs/WINDOWS-CLIENT.md before modifying Windows client. No real packages approved and no signed production desktop EXE; the GUI is a prototype with installation disabled until owner-curated mapping exists.
- Next focus: upstream-based Android client and true release signing/provenance. Never request owner desktop input when hosted runners can complete a trusted engineering check.

## Android native preview tranche (2026-11-02)
- Read docs/ANDROID-CLIENT.md, scripts/build_android_catalog.py and .github/workflows/android-client-preview.yml. Adds Android Java RTL offline catalogue; reuses separately installed upstream F-Droid through a verified-origin ACTION_VIEW handoff, **not** by forking or embedding F-Droid's GPL installer code.
- New Android workflow must pass genuine Gradle compile and artifact checks before claiming success. Debug key is ephemeral; never treat it as a production signing identity.
- catalog/android_repository.json is null; no independent verified F-Droid signing key/index or approved Android packages exist; all install buttons remain disabled.

## Hosted Android emulator QA (pending check)
- Workflow `.github/workflows/android-emulator-smoke.yml` provisions an isolated GitHub-hosted Android emulator, launches the native activity and verifies accessibility nodes show F-Droid installation disabled. This is **not** physical-device install/update acceptance. Check actual CI run before claiming success.

## Native Android + hosted emulator accepted (2026-11-02)
- Feature PR #17 merged at `4688fb18294a1e05ec3f3cf357c6a456a84009fb`. Hosted Android Gradle CI built and verified a debug-key APK. PR build: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41487326775 ; main build: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41487682003. Both succeeded.
- Emulator PR #18 merged at `56fe430abab33d4c4a843296778ed39c480e860e`. Hosted Android UI smoke succeeded: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41488084733 ; captures UI hierarchy and screenshot and proves F-Droid button disabled.
- Next check latest main CI and emulator rerun. The preview APK is debug signed, not production. No trusted F-Droid repo or accepted third-party APK exists. Never equate emulator smoke success with signed repo installation/update or real device QA.

## Native artifact provenance (2026-11-02 engineering tranche)
- New docs/NATIVE-PROVENANCE.md and scripts/attested_binary_receipt.py: GitHub-native signed build attestation and strict gh CLI verification for Android debug APK and unsigned Windows EXE, main-only, builder workflow/commit pinned. JSON receipt alone never proves cryptographic validity.
- The attestation verification jobs run ONLY after their own trusted-main build job; do not claim success before inspecting the real Actions results after merge. This does not verify developer APK/Authenticode release signatures.

## Build provenance accepted; F-Droid preflight in progress (2026-11-02)
- PR #20 merged main SHA 5429ee5d259b138c7478a5c15b226c4b995c1d5b. Android provenance run https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41491331966 and Windows provenance run https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41491331958 both SUCCESS, with independently verified GitHub attestations and short-lived receipt artifacts. Full native CI/CodeQL/owner Windows checks also passed.
- The new F-Droid signed-index preflight uses official fdroidserver verification only after independent URL+fingerprint pins. See docs/FDROID-INDEX-PREFLIGHT.md; do not claim live signature acceptance since catalog/android_repository.json is still null.

## Confirmed 2026-11-02 native provenance and index preflight
- Native preview provenance PR #20 merged SHA 5429ee5d259b138c7478a5c15b226c4b995c1d5b: Android attestation+gh verify https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41491331966 and unsigned Windows EXE attestation+gh verify https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41491331958 both successful. This is NOT publisher release signing.
- F-Droid signed-index preflight PR #21 merged SHA 0da534fd3e658ed2398a031b71da43043e76a4df: Linux+Windows CI, trusted owner Windows QA, CodeQL and Pages successful. Scripts reuse fdroidserver index-v2 verifier but all tests are mocked; no production repository has been signed, verified or registered. catalog/android_repository.json still null.
- Future agents must prioritize actual trusted signer and two-version install/update rather than adding more paper gates. Owner approval and safe persistent signing key custody must be isolated, never fabricated.

## Real F-Droid signed-index sandbox acceptance (pending workflow)
- Script scripts/fdroid_signed_repo_drill.py and hosted-main workflow .github/workflows/fdroid-signed-index-drill.yml build a throwaway F-Droid repository with upstream fdroidserver from our native debug APK. They must verify an actual signed v2 index and reject wrong fingerprint/tampering. Read docs/FDROID-ISOLATED-SIGNED-INDEX-DRILL.md before running or editing.
- Ephemeral signing material is created ONLY in temporary GitHub-hosted Ubuntu workspace; no test key/config/index or debug APK from the drill is published. Production signer registry and repository remain empty/null. Check real GitHub workflow run before claiming acceptance.

## Native Android two-version emulator upgrade (pending acceptance)
- Hosted workflow .github/workflows/android-two-version-smoke.yml builds ephemeral preview versionCode 1 and 2 under SAME debug key, installs and upgrades on real Android 35 emulator, rejects a downgrade, and confirms RTL UI still disables unapproved F-Droid button. See docs/ANDROID-TWO-VERSION-SMOKE.md; check actual Actions acceptance before claiming pass.
- This is Android system DEBUG upgrade only, NOT an update from a signed F-Droid production repo or approved real app. No APKs or signing keys uploaded.

## Android package rejection QA extension (pending acceptance)
- The two-version emulator workflow also tests an independently debug-re-signed update and a truncated APK; both must be rejected without replacing installed v2. Only hosted CI, no owner desktop and no test keys/APKs uploaded. Require real workflow success before claiming acceptance. See docs/ANDROID-TWO-VERSION-SMOKE.md.


## Consolidated engineering acceptance and stable root handoff (2026-11-02)
- New root `NEXT-EXECUTION.md` points to canonical `docs/NEXT-EXECUTION.md`; read both after this file in new chats, and verify live GitHub checks.
- PR #27: hosted Android 35 two-debug-version upgrade and downgrade denial, merged `df47991144c4a226fe76552cadbf351b1bc7c197`. Feature run https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41498803142 and merged-main run https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41504126166 were SUCCESS.
- PR #28: Android foreign-signer and truncated APK rejection plus installed-v2 continuity, merged `1a5e43a4e59d1ce17966c83d6042eb78127fe681`. Feature emulator https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41504576824, CI https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41504576692 and CodeQL https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41504576810 all SUCCESS; main emulator https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41505157772 also SUCCESS.
- PR #29: reviewed immutable web launch origin and release-history metadata gate, merged `eb08797a42fdde5cfacd0f6542ee0100d02bb680`. Feature CI https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41505384878, CodeQL https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41505384980, hosted Android https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41505384967 and Windows preview https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41505385179 all SUCCESS. Latest main checks must be independently rechecked after merge.
- `catalog/trusted_web_origins.json` and `catalog/web_release_history.json` are EMPTY. Static approval metadata is NOT real HTTPS deployment-content validation. The Android negative tests use ephemeral debug keys, not production publisher signing.
- Release blockers remain independently approved developer certificates, persistent offline F-Droid signing key + backup, real signed public index and client subscription, actual signed production APK/EXE, true F-Droid app update and owner-device acceptance. Never enable public downloads on a fabricated fixture.


### Recheck after PR #29 merge: main green
At main `eb08797a42fdde5cfacd0f6542ee0100d02bb680`, actual GitHub Actions runs for CI #41505611808, CodeQL #41505612155, owner-trusted Windows QA #41505612176, Android preview #41505612008, Windows EXE preview #41505612132, Pages #41505611948 and PWA evidence #41505612012 all completed SUCCESS. The preview APK remains debug-signed, the EXE unsigned, and both web origin registries remain empty.

## Integrated engineering batch (2026-11-02; pending real PR acceptance)
- The cross-platform branch `feature/integrated-technical-closure-20261102` implements safe PWA planned-only offline fallback, observed WinGet execution without false installed-state claims, actual GitHub attestation verifier with pinned producer/source identity, and a combined OS signature + source provenance release-review gate. Read `docs/INTEGRATED-GAP-MATRIX.md`.
- Recheck actual hosted Linux/Windows CI, CodeQL, Android emulator and unsigned Windows preview workflow results before claiming acceptance. Trust registries remain empty. Do not treat mock tests as real production signature or malware approval.

## F-Droid independent keystore backup engineering (2026-11-02; pending PR acceptance)
- Read docs/FDROID-KEY-CUSTODY.md: offline POSIX owner-only independent-volume backup with byte verification, strict file perms, no symlinks/overwrites, no key uploads. Public CI tests dummy bytes only. Do not claim actual owner offline backup or production signer provisioning.

## Windows real installed-state readback (2026-11-02 pending PR acceptance)
- See docs/WINDOWS-CLIENT.md and windows_client/installed_state.py. Actual WinGet JSON export is used before and after approved install/upgrade; rejects downgrade, unknown or mismatched installed version and does not equate manager exit=0 with success. No approved WinGet mappings exist. Check real hosted CI and Windows preview workflow before claiming acceptance.

## Real Chromium PWA UI and offline QA (pending workflow)
- Workflow `.github/workflows/pwa-browser-acceptance.yml` exercises native app detail dialog, search/filter, real Chromium service worker and offline-only planned catalogue. Read docs/PWA-REAL-BROWSER-QA.md. Require actual Actions success + safe screenshot before accepting; this does not verify signed binaries or production publisher accounts.

## Integrated 2026-11-02 engineering execution — actual merged results
- **Read docs/ENGINEERING-CLOSURE-2026-11-02.md** for the authoritative dated acceptance and gap ledger. PRs **#33, #34, #35, #36, #37** all merged, with exact main SHAs and live Actions evidence. Main at PR #37 merge SHA `8a76c419e581506d395e9eb6e016425d9afa2ca1` completed hosted Linux/Windows CI, CodeQL, owner-trusted Windows QA, Pages, reproducible PWA evidence and REAL Playwright Chromium browser/offline acceptance — all SUCCESS.
- The genuine browser test exposed and fixed a real localhost-only PWA Service Worker registration bug; secure loopback IPv4 127.0.0.1 now works. Other work: offline planned-only PWA, Windows installed-state readback, signed GitHub provenance review, isolated owner keystore backup tooling, application details/changelog.
- **Engineering result PARTIAL, production readiness NOT accepted.** Real publisher signers, stable offline F-Droid signer and verified signed public repository/client install, owner-approved app release, signed Windows installer/real-device updates, full publisher portal and branch ruleset remain incomplete. Do not fabricate release or key approval.

## Review-only release governance and real source security scan (2026-11-02; acceptance pending)
- Branch `feature/secure-release-governance-and-supply-chain-20261102` adds cross-platform publisher trust identity correction, PR-only atomic revocation plan for exact release / whole signer, owner-review-only integrated promotion proposal, and upstream pinned Trivy source vulnerability/secret/config scan + CycloneDX SBOM. Read `docs/RELEASE-GOVERNANCE.md` and `docs/SUPPLY-CHAIN-SCAN.md`. Neither source scanning nor proposal authorizes live package distribution. Verify exact CI/CodeQL/Trivy run + merge before marking accepted.

## Actual Android debug manifest permission acceptance (2026-11-02; pending green checks)
- The hosted native APK workflow invokes official `aapt` against the newly assembled debug APK and checks reviewed exact version and manifest permission allowlist in `catalog/android_preview_permission_policy.json`. See `docs/ANDROID-PERMISSIONS.md`. Do not claim malware detection or production signer proof from permission names. Require actual workflow success and artifact receipt before acceptance.

## Real mobile Chromium accessibility QA (pending genuine workflow evidence)
- The browser acceptance workflow now runs pinned axe-core on mobile-sized actual Chromium for serious/critical WCAG2.1 A/AA checks across dark/light/native-dialog states, horizontal overflow and keyboard/escape navigation. See docs/PWA-MOBILE-A11Y.md; do not mark as passed until actual workflow success. This is not a full screen-reader/physical-device audit.

## Second integrated engineering run (2026-11-02) — six real merged PRs
- Read `docs/ENGINEERING-CLOSURE-2026-11-02-RUN2.md` for exact PRs, main SHAs, workflow run URLs, source supply-chain scan, actual Android permission aapt acceptance, mobile axe accessibility findings/fixes, and safe official GitHub Actions upgrades (#39, #40, #41, #5, #6, #4). Final latest main target `86b47e7839c4c63f722da448ebdee1f3fcda163c` — **verify terminal actual workflows before declaring all main checks green**. No first-party publisher identity or signed production release is approved; full engineering state remains PARTIAL.

## Actual binary archive and owner-local publisher preflight — 2026-11-03 (CI acceptance pending)
- Inspect `docs/REAL-BINARY-INTAKE.md`, `scripts/binary_archive_review.py` and `scripts/owner_candidate_intake.py`: source + signed GitHub producer verification, actual Android APK archive CRC/traversal/ZIP-bomb inspection, Android manifest reviewed permissions and before/after SHA-256 on same artifact. Native debug APK CI runs archive scanner on real bytes. Public CI fixtures are not real production malware clearance, publisher credentials or owner approval; no public downloads registered.

## Actual owner-operated Pages HTTPS byte parity (2026-11-03)
- Read docs/REAL-PAGES-HTTPS-ACCEPTANCE.md: source-built public site bytes are compared via certificate-verified HTTPS against the live Pages origin, with redirects and mismatches denied in PR preflight and after production Pages deploy. This is FIRST-PARTY storefront parity only, not an approved third-party web app or product release. PR #44 requires exact CI/CodeQL/live preflight and merged-main Pages verification.

## Actual ClamAV on real APK/EXE bytes (2026-11-03; acceptance pending)
- Read docs/ACTUAL-ANTIVIRUS-SCREENING.md: owner local intake runs real ClamAV with recent signature DB and exact artifact rehash, fails on detections/errors; hosted first-party debug APK workflow refreshes DB and scans real APK. A non-detection never proves malware absence or authorizes public release. Verify real CI and scanner receipts before accepting.

## Integrated 2026-11-03 actual binary/security/deployment execution — accepted
- **Read `docs/ENGINEERING-CLOSURE-2026-11-03.md` as the latest engineering ledger**. Source PRs #43/#44/#45 merged, final main `e11f32ae3773e7b5488545230a1e96e27ed8dae4`, all eight exact-main workflows SUCCESS. Verified a real first-party APK ZIP/archive CRC+traversal/ZIP-bomb check, owner-local developer signer+GitHub provenance+Android permissions+SHA preflight, actual fresh ClamAV DEBUG APK signature scan, and live HTTPS bytes parity of published first-party Pages. No genuine production publisher, malware-free certification, signed repository, private app release, official F-Droid client subscription or signed Windows owner installation has been accepted. Entire engineering verdict **PARTIAL**.

## Owner-private publisher quarantine engineering (2026-11-03; pending real PR acceptance)
- `scripts/private_publisher_inbox.py` is a **POSIX owner-local quarantined intake queue**, NOT an Internet upload server or authenticated multi-tenant portal. It creates private 0700/0600 per-submission actual file copies; checks exact SHA/size and archive structure; denies symlink/hardlink, duplicates and path misuse; records no-approve event ledger; allows only review-requested exact bytes to enter real `owner_candidate_intake.py` crypto/ClamAV checks. Read `docs/PRIVATE-PUBLISHER-QUARANTINE.md`. All identity, signature, malware clearance and publication flags remain false. Verify actual CI before declaring engineering acceptance; genuine publisher auth/keys/production service remain outstanding.

## Strict F-Droid staging anti-bypass (2026-11-03; pending verified PR checks)
- Old `fdroid_bridge.stage()` signed-APK-only path is now invalid. Read `docs/FDROID-STRICT-VERIFIED-STAGING.md`: before even staging, full cryptographic signed GitHub provenance, pinned developer certificate, official Android permissions, actual archive checks, fresh ClamAV and private POSIX signer workspace are mandatory; no publisher approval, signed repo/client subscription, or public deployment is inferred. All negative CI fixtures are synthetic. Merge only after actual hosted Linux/Windows and CodeQL/Trivy checks.

## F-Droid index-v2 exact APK and repository signer private verification (2026-11-03; PR pending)
- `scripts/verify_fdroid_private_stage.py` now invokes upstream `fdroidserver.index.get_index_from_jar`, checks separately supplied exact private repo signer fingerprint, JAR-signed SHA/size for `index-v2.json`, and uniquely indexes exact APK package/versionCode/versionName/hash/size. `fdroid_bridge.py` requires this after `fdroid update`, locks private workspace on failure instead of claiming rollback. See `docs/FDROID-LOCAL-SIGNED-INDEX-ACCEPTANCE.md`; independent hosted disposable actual F-Droid signed-index workflow runs on same-repo PRs, never owner/self-hosted keys. Not proof of live HTTPS signer approval or official client/device install.

## Latest integrated engineering acceptance, 2026-11-03 — source SHA 562d4cd
- Latest ledger: `docs/ENGINEERING-CLOSURE-2026-11-03-RUN4.md`. PRs #47 (owner-private POSIX publisher quarantine), #48 (close legacy signer-only F-Droid staging bypass) and #49 (real upstream signed local index-v2 and unique exact APK/hash/version binding) merged on `main` `562d4cd808a73e11a139ab52f5ee4adbe50ef107`. Hosted CI, CodeQL, Trivy, actual disposable F-Droid index+APK test, Pages and reproducible build completed SUCCESS. Trusted-main owner Windows QA run #41587826538 QUEUED on latest check; do not claim its acceptance before completion. No authenticated publisher web service, real production F-Droid signer/index/client subscription, independent owner signing approval, private release or actual owner-device install. Engineering verdict PARTIAL, production NOT APPROVED.

## Latest actual integrated engineering PRs #51–#53 (2026-11-03)
- Read `docs/ENGINEERING-CLOSURE-2026-11-03-RUN5.md` for exact feature/main SHAs, successful actual hosted CI/CodeQL/Trivy, actual local loopback publisher upload, actual two-debug-version F-Droid signed-index+APK byte continuity, and real independent-volume disposable F-Droid key loss/restore/re-sign acceptance.
- PR #51 merged `e789a5bfc68aab903d293bdb8397a032344f083c`, PR #52 merged `77040243f0308d14d0aef81bf8edffceaf4d6912`, PR #53 merged `1340cea7c8ea43d877e0d77bfde1a80763d4c0b2`. **Never count a queued self-hosted owner Windows job as success.** Verify live main workflows anew.
- Local publisher bearer token is a PRIVATE localhost transport credential, not a real registered publisher account; no public ingress, no approval, no release. Ephemeral test backup and JAR signatures are not owner production key custody, public HTTPS repository or official F-Droid Android client installation. Protected main ruleset Issue #31 and production signer/device/service approvals remain pending. Full engineering PARTIAL, no production publication.

## Actual official F-Droid client integration — 2026-11-03 RUN6
- Read `docs/ENGINEERING-CLOSURE-2026-11-03-RUN6.md`: PR #55 merged `30f863579e290bffa78f4ffe59726605296f30d6` with eight exact-head successful workflows, and eleven exact-main hosted workflows SUCCESS. Official upstream F-Droid APK's real GPG signature and pinned Android signing certificate were verified, APK installed on real hosted Android 35 emulator and `fdroidrepos://` handoff accepted by its real activity/process. Its UIAutomator dump FAILED to provide a hierarchy (`ui_hierarchy_verified=false`); it did NOT add a real repository or install/update an app from F-Droid.
- Win32 Authenticode signing real CI PR #56 is an independent **unaccepted** candidate pending actual hosted signing workflow result; source CI alone never establishes a Windows signed EXE. Check live PR #56, do not merge red or in-progress checks. Full engineering PARTIAL, no owner publisher/repo trust root or production release.

## RUN7: actual portable Authenticode on real Windows PE accepted (2026-11-03)
- Canonical exact source/merge/main checks: `docs/ENGINEERING-CLOSURE-2026-11-03-RUN7.md`. PR #56 now merged main `2cd503aa0247f73de960137ca45a4c85b21edf61`. Actual hosted Windows PyInstaller unsigned EXE plus separate hosted Linux `osslsigncode 2.8` PE signing/checking under two disposable root→code-signer identities: real signature/certificate pin + unsigned/wrong signer/wrong root/tamper negatives SUCCESS [run #41611354053](https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41611354053). Exact CI/CodeQL/Trivy on feature and six applicable main-hosted checks SUCCESS. Owner Windows trusted QA still QUEUED, NOT PASS.
- **NOT** native WinVerifyTrust, production Authenticode/CA, first authentic publisher release, official F-Droid signed repo client actual install/update, Windows signed installer/WinGet, physical consented QA, public origin/production key custody or main ruleset Issue #31. No public download permission; engineering still PARTIAL. Prior failed native hosted cert-store attempts must not be relabeled green. Continue whole-project technical closure, not more duplicate signature microfixes.

## RUN8 real integrated delivery (2026-11-03) — source history and strict next batch
- Read `docs/ENGINEERING-CLOSURE-2026-11-03-RUN8.md` and live GitHub first. Actual PR #59 HTTPS TLS1.2+ verified-chain/hostname+independent leaf-pin authenticated publisher quarantine merged `33a18fcbe713cea5416bdd6f8b1f28ef12129b42`; POSIX private tenant disk/quota, real OpenSSL TLS negative tests, CI/CodeQL/Trivy SUCCESS. No remote production deployment, verified publisher account or release.
- PR #60 merged `c437292514504114f8852ebb49d0bb21c596ee32`; corrected malformed F-Droid scheme nesting to preserve real approved hostname/path/cert pin, all eight actual hosted Android/CodeQL/Trivy/official-client intent checks SUCCESS. Still no official client signed repo install/update.
- PR #61 merged `c53f6f1403d5836882238a980003a4f517e4fdfc`; real free NSIS 3.11.0 per-user **UNSIGNED test-only** Windows installer packaging actual PyInstaller EXE, real isolated hosted Windows v1 install/v2 installer upgrade/older downgrade rejected/actual uninstall and HKCU cleanup, plus genuine PE Authenticode and CI/CodeQL/Trivy SUCCESS; six main hosted checks SUCCESS. No distinct app binary v2, production installer signer/WinGet/physical Windows device approved. Trusted owner Windows QA still QUEUED.
- PR #62 (`feature/official-fdroid-real-test-repo-on-emulator-20261103`) is genuine disposable signed-repo + official Android client **network-fetch** integration under active debug; may FAIL genuine hosted emulator. Do NOT count it accepted until exact-head real Android job SUCCESS; no fake subscription or in-client APK install/upgrade claim.
- Product-wide engineering PARTIAL; production signer/repository HTTPS/publisher identity/owner-admin protected main ruleset #31/physical consent missing. Never enable public releases from synthetic CI.

## RUN9 verified merged native/network engineering (2026-11-03)
- Latest canonical evidence `docs/ENGINEERING-CLOSURE-2026-11-03-RUN9.md`: PR #64 merged `69cffd6753a8391ac5d9dcfdea5eccf30c172503`, atomic owner-private publisher bearer rotate/revoke (running HTTP and HTTPS immediate denial, actual TLS tests) PASS. PR #62 merged `9c2c14ba1b5270657ff0ac9250dcdb3e45233dfc`, real official F-Droid APK HTTPS signed index v1 and v2 network GETs from isolated Android emulator PASS, not repo DB install/upgrade. PR #65 merged `e8bb47027087d63bd0f9cb467011b393dbd7a98b`, actual source-distinct native Win EXE v1→v2 unsigned NSIS installer upgrade, downgrade rejection/uninstall on hosted Windows PASS. Exact feature CI/CodeQL/Trivy and six main hosted checks success. Owner Windows QA queued; no production signer/app or main ruleset. PR #66 native official app SQLite persistence proof is **candidate, not accepted unless real emulator job green**.
- Engineering PARTIAL, public production binaries disabled; next autonomously complete real in-client F-Droid install/update, publisher account/release governance and production-compatible Windows acceptance tools where possible, with actual owner-only gates separate.

## RUN10 accepted Android native repository and Windows trust boundary (2026-11-03)
- **Actual main acceptance**: PR #66 merged as `69afc50039cbc0e649309a51e8c224b32d87674c`; genuine official F-Droid Android 33 client used its **real clickable UI**, signed disposable repo v1/v2 network requests, and independently probed the genuine native SQLite repository entry after UI confirmation. Exact last feature Android #41641634305 SUCCESS, latest main Android #41642708651 SUCCESS; no proof of in-client APK installation, upgrade or native DB signer pin.
- **Truthful Windows gate**: original PR #68 native Windows positive trusted-signer test #41642192393 TIMED OUT on test CurrentUser certificate-store manipulation. Revised still-open PR #68 tests real Windows native **rejection** of ephemeral untrusted signer certs without store writes, not trusted production CA acceptance. Check exact-head Actions before merging. Keep genuine positive WinVerifyTrust, owner signer and WinGet release gates open.
- [RUN10 evidence and next work](docs/ENGINEERING-CLOSURE-2026-11-03-RUN10.md). Do not regress actual F-Droid signed client SQLite readback, falsely mark private test CA as owner production, bypass review/branch rulesets or create public downloads. Issue #31 protection and external owner gates remain.

## RUN11 verified Windows negative trust and remaining positive gate (2026-11-03)
- PR #68 merged on main as `97e33b34f4db2e44280570072d93c25cc6c8e679`: exact-head feature native Windows run #41644875439, CI #41644875129, CodeQL #41644875074, supply chain #41644875322 SUCCESS. Real Windows SDK SignTool signs two different disposable leaf-certificate EXEs and native Authenticode sees their pinned signer identities while reporting `UnknownError` rather than `Valid`; unsigned and tampered refused. This verifies only **fail-closed native OS observations**; native production trusted certificate approval is FALSE. No Windows CA test store changes.
- Source of truth [RUN11 ledger](docs/ENGINEERING-CLOSURE-2026-11-03-RUN11.md). PR #66 actual official F-Droid native SQLite repo acceptance and RUN10 still valid. The main remaining engineerable gates: actual in-client signed v1 APK install→v2 upgrade+source verification, repo DB certificate pin readback, publisher identity/MFA/auth review and production-compatible Windows trust implementation; external owner-only gates untouched.
