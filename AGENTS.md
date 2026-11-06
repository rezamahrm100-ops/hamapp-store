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

## RUN12 verified official F-Droid native SQLite signer binding (2026-11-03)
- PR #71 was **actually merged** as `892e75d1032c4791f3a241736d1bd2650109dfd5`. Real hosted Android 33 signed client #41646828386 SUCCESS on exact feature head `88a33ab26b052882bc9d547cbc2d3fe51e00ab0e`; hosted CI #41646828475, CodeQL #41646828491 and supply-chain #41646828341 SUCCESS. Verified the REAL official F-Droid app's native SQLite `CoreRepository.certificate` hex DER SHA-256 equals independently verified disposable index-v2 JAR signer pin, with one unique matching repo address, read-only DB integrity and false-signer/duplicate/malformed negatives. No owner key, app install or public release acceptance.
- PR #72 candidate real official client **in-app v1 install + v2 upgrade**, with exact UI interaction, APK GET, Android package-manager byte/signer readback, is **NOT ACCEPTED UNTIL EXACT-HEAD REAL EMULATOR JOB SUCCESS**. No `adb install`, synthetic SQL, permission bypass or owner hardware allowed. On failure preserve actual CI error, do not mark it complete. Full ledger `docs/ENGINEERING-CLOSURE-2026-11-03-RUN12.md`.

## RUN13 verified F-Droid Add consent and still-blocked actual app install (2026-11-03)
- PR #75 merged `11e70a5633b308a97b71ecebea66b596f55655b4`. Real official F-Droid Android feature run #41655629539 and CI #41655629657, CodeQL #41655629684, supply-chain #41655630875 all **SUCCESS** exact feature SHA `27dd7ef58253ab3c40f27244026692d1bd1a33f1`. Generic F-Droid controls now NEVER click `Add repository` / system `Allow`; dedicated live bounded consent click only, genuine signed index v1/v2 network + native SQLite CoreRepository certificate SHA256 pin preserved. Postmerge main Android #41656844438 was in progress at ledger creation, so recheck live.
- Actual F-Droid in-client APK v1 install/v2 upgrade PR #72 remains **unmerged and unaccepted**. Exact test #41654899145 failed after real repository consent; screenshot/diagnostic showed APK Install input sent but Android PM version still null, no metered dialogue or system permission prompt visible at end. New head `b3c47d6cee5d158c89355a92626d86fc8d9683df` adds disposable early-action screenshot, exact APK GET count and bounded Boolean error categories, not fake install. Real job #41656738400 pending/in progress when checkpoint written; retrieve its artifact before changes. Production keys, owner devices, branch ruleset #31 remain separate gates. [RUN13 ledger](docs/ENGINEERING-CLOSURE-2026-11-03-RUN13.md).

## RUN14 verified native Windows custom-root CA and exact Android sideload blocker (2026-11-03)
- PR #77 MERGED `34d4d0f06be5b6171bd8a39241fa78e708e34374` after exact-head CI #41660197171, CodeQL #41660197582, security #41660197276, real Windows multi-job #41660197319 all SUCCESS. Actual hosted Win SDK SignTool signs real PE with two disposable CA→EKU CodeSigning leaves; native .NET `X509Chain` with *in-memory only* `CustomRootTrust` accepts correct roots and refuses swapped roots. Windows Get-AuthenticodeSignature still reports `UnknownError`, **NOT Valid/production trusted**. No OS certificate store writes, owner key, release or device approval. Main postmerge Windows #41661531342 was running at report time; check live.
- Actual independent official F-Droid app install PR #72 remains UNMERGED. Real Android #41659125811 proved a genuine signed APK v1 client GET but Android native security displayed **F-Droid is not allowed to install unknown apps from this source → Settings**; no actual PM-installed app. New exact-head `94f2872c0f09c321162fc4b6fb71c42de1ebddc2` tests navigating actual F-Droid-specific OS Settings permission via genuine Settings + unique unchecked Allow-from-this-source switch and independently reading checked=true, **only disposable hosted emulator**, no adb shell appops/grant/settings put or owner device. Exact Android #41661386351 still unaccepted pending real CI outcome. Source CI/CodeQL/security green at timestamp; merge only on real native install v1→v2 + digest/cert + APK GET. Full report `docs/ENGINEERING-CLOSURE-2026-11-03-RUN14.md`.

## RUN15 actual official F-Droid v1 installed; v2 saved-repository refresh in progress (2026-11-03)
- Actual isolated hosted Android #41661386351 **proved genuine official F-Droid in-client v1 install**: on-screen F-Droid-specific source Settings consent, real client APK GET, native Android PM versionCode 1, installed APK byte-for-byte SHA256 and developer signer match. The full **v1→v2** job failed because after signed v2 index *preview* request, official details still showed Open, no Update, no v2 APK GET. This is engineering partial, NOT complete F-Droid lifecycle or owner-device approval.
- PR #72 latest feature head at this checkpoint `b71cc6fe79b0c530bf0f12af29a58cd441f47c8e` adds a new isolated official F-Droid **saved repository UI** route: actual Discover Repositories → exact disposable test repo → repository Details `Check for updates` button, which upstream connects to RepoUpdateWorker. It refuses unrelated packages, nonclickable/ambiguous buttons, static coordinates, direct app installation and SQLite edits. Exact-head hosted CI #41688262861, CodeQL #41688262831, supply-chain #41688262938 SUCCESS; real Android #41688263014 in progress at report snapshot. DO NOT merge until real v1 and v2 native APK byte/signer/version + actual client APK GET and exact Android job SUCCESS. Read [RUN15](docs/ENGINEERING-CLOSURE-2026-11-03-RUN15.md).
- Other owner/external gates unchanged: production signed origin/key backup/verified publisher, official certificate and real owner device trust, main protection Issue #31, trusted Windows owner runner queued. Do not enable public downloads.

## OWNER TEST DELIVERY (2026-11-03) — delivery is now prioritized over real in-client install integration
- User explicitly asked: stop spending each run on reproducing real hardware/in-app F-Droid install/update; deliver **installable native Android/Windows previews** for the owner to install and test, and continue remaining coding in integrated batches. This does **not** override security, release gates or justify falsely marking engineering complete.
- PR #80 merged main `4213d05f76a46417db135e487a4c7246d2dd3aba`. Exactly that main SHA hosted owner-preview build #41696010045 SUCCESS for both real native Android and Windows jobs, Android DEBUG APK (15,214 bytes, SHA256 `75d37f7da4377f3c12e8291d050de16a7a4705ca9d8892f28c53fb4c799bfed8`), Windows portable unsigned EXE (11,406,183 bytes, SHA256 `0e86962cdaded1fc8a08b8676bb5c0f3e4d78da62d85381c22eccfc7867b8a97`) and genuine optional per-user unsigned NSIS setup (11,175,851 bytes, SHA256 `2be171bcd40537cedf19c42097fe4fc5d30114ad82666df3c9e0940117e086b2`). Artifacts `HamApp-Android-Owner-Test-APK` and `HamApp-Windows-Owner-Test-EXE-Setup` each include `manifest.json`, `README_FA.md`, SHA256SUMS; retained 7 days in the actual GitHub main workflow. No production signer/owner device verification.
- Main #41696010370 CI, #41696010035 CodeQL, #41696010205 source supply-chain, #41696010036 Pages, #41696010141 reproducible evidence and #41696010045 owner preview all SUCCESS. Owner Windows self-hosted QA #41696010226 QUEUED, not success. Public download catalogue intentionally empty; main protection Issue #31 still owner/admin gate.
- PR #72 separate F-Droid v1→v2 exact UI/native integration remains OPEN, without verified full upgrade. It is **NOT a blocker for owner preview download/installation**. Do not claim a full commercial store, trusted Windows publisher, production Android signature, real released app catalogue or public installer. [Owner installation and exact remaining scope](docs/OWNER-INSTALL-TEST-HANDOFF-2026-11-03.md).

## UI-backend reuse tranche — candidate PR #82 (2026-11-04)
- Read `docs/UI-BACKEND-CONTRACT.md` before the next branded interface development. The native engines remain upstream F-Droid companion + fdroidserver and Microsoft WinGet, with a new deterministic `hamapp-ui-backend-v1` read model for all 3 platforms. Do not vendor UniGetUI's entire GUI or misrepresent F-Droid GPL obligations.
- Shared contract is **not** an installation authority: each OS client rechecks approved metadata and requires user/OS consent. Public release registry stays empty; existing production signers and private approvals remain mandatory.
- PR #82 is a CANDIDATE until hosted CI, Android/Windows native previews and postmerge evidence are independently green. Real F-Droid v1-to-v2 client update remains separately tracked in PR #72.

## Accepted UI-ready upstream engine integration — 2026-11-04

- PR #72 merged to main at `791b1c562ba310e4f592fdfa7f9103bf416d066b`. Exact-head official F-Droid real in-app install/upgrade emulator workflow #41694151059 succeeded: disposable signed Android v1 and v2 APKs were obtained by official client, PackageManager installed version/bytes/signers checked. This is NOT a real publisher release, approved production signing key, or owner phone test.
- PR #82 `feature/ui-ready-upstream-adapters-20261104` merged after all 12 exact-HEAD GitHub workflow runs succeeded at `f3dbd0f2d1c5e3fae5ccee877d035e3594342ee4`. CI #41893624391, Android native #41893624649, Windows native #41893624475, owner installable previews #41893624072, browser #41893624266, CodeQL #41893624789, hosted source scan #41893624377, ClamAV #41893624580, official F-Droid intent #41893624157, F-Droid real install+update #41893625232, Android emulator UI #41893624831, Android two-version #41893624806: ALL SUCCESS.
- UI-ready read-only contract is `docs/UI-BACKEND-CONTRACT.md` and `scripts/build_ui_contract.py`: `hamapp-ui-backend-v1` emits shared approval-gated capabilities for native Android, native Windows and PWA. `FdroidEngine.java` isolates official companion launch from Android presentation. Official F-Droid + fdroidserver and native WinGet remain the package-management engines; DO NOT vendor entire UniGetUI GUI merely to use WinGet.
- Next user requested phase: bespoke Persian RTL UI/UX in Android, Windows and web, on top of **existing execution/trust engines**, no duplicate package manager. Preview APK (DEBUG) and Windows EXE/NSIS (unsigned) compile; they are not production-approved. All public download approvals remain disabled. Owner-held production signer identities, durable F-Droid repo key and independent backup, approved origin, genuine first publisher/release, owner-device acceptance and marketplace operation are external/product release gates, not solved by this UI-bound engineering tranche.

## 2026-11-04 — usable personal previews with public upstream sources: ACCEPTED

PR #84 merged on main `7095d11c4ca1210014ad279f05ef1b4eb737f13d` after **all 12** exact-head hosted workflows succeeded on `bc2019f44ad733b07bbcfc7e490c680c329142b1`. Read `docs/USABLE-PREVIEW-UPSTREAM-2026-11-04.md`.
- Android: owner-installable debug APK now has an explicit opt-in launcher for the **separately installed official F-Droid client** (or fixed official website if absent), plus app details. This does NOT grant HamApp direct APK install authority; the private signed-repo handoff stays disabled without approved releases.
- Windows: owner-installable unsigned portable EXE + NSIS setup now includes separate WinGet public source search/detail and explicit third-party interactive install/upgrade, strict package identity, source pin, no automatic EULA/UAC acceptance and installed-state readback. This is NOT an owner-approved package or verified vendor signature; the HamApp-owned catalogue remains planned-only.
- Web: separate upstream informational links, live Chromium accessibility and safe offline fallback. All new functions have negative security tests; full GUI and owner-device acceptance are still outstanding.
- Owner artifacts run #41898734093: Android `HamApp-Android-Owner-Test-APK` and Windows `HamApp-Windows-Owner-Test-EXE-Setup`, includes hashes and Persian instructions. Debug Android and unsigned Windows are preview-only, not production.
- Next active goal: **install and use/test these exact preview binaries**, fix observed owner-device issues, then finish bespoke Persian RTL native UI. Production publisher identities, stable repo signer/offline backup, approved public downloads, Windows production signing and branch protection remain separate external gates. Do not erase this real-use capability while redesigning UI.

## Accepted Atlas UI open-source integration — 2026-11-04

- PR #86 merged onto main commit `af33be11479a8728a27387a67b0030a58613b4e3`, exact tested head `754dec30f0bfc1445cb9c919cdc02d97db2849c9`, after **all 12** relevant GitHub Actions concluded SUCCESS. The next campaign must not recreate native package managers or restart UI framework evaluation.
- Implementation: native Android Java Google Material Components **1.14.0** Apache-2.0 with Material 3 Views and branded RTL; Windows native Tkinter **ttkbootstrap 2.2.6** pinned and packaged with PyInstaller plus stock ttk offline development fallback; PWA locally authored premium responsive RTL styles based on Tabler visual patterns, **no vendored Tabler code / remote CSS**. See `docs/ATLAS-UI-OPEN-SOURCE-INTEGRATION.md`.
- AndroidX Material transitive app-scoped broadcast receiver guard `ir.hamapp.store.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION` was observed through actual SDK aapt, added to exact approved debug APK allowlist with strict negative tests; no INTERNET, REQUEST_INSTALL_PACKAGES, or arbitrary permission accepted. React/Compose/Qt migration is unnecessary for current delivery.
- Same-head acceptance runs: CI #41910093358, CodeQL #41910093313, real Chromium/WCAG2.1AA/offline #41910093373, Android native APK + permission review #41910093372, owner APK+EXE/NSIS previews #41910093475, Windows EXE+isolated installer lifecycle #41910093274, Android emulator UI #41910093452, Android two-version upgrade #41910093314, official signed F-Droid intent #41910093310, real F-Droid in-client signed repo install/upgrade #41910093744, ClamAV #41910093465, supply-chain scan #41910093638, ALL SUCCESS.
- Owner download artifacts (short lived): #41910093475 Android `HamApp-Android-Owner-Test-APK` ID 13361458489; Windows `HamApp-Windows-Owner-Test-EXE-Setup` ID 13361933549. They remain **DEBUG signed** and **UNSIGNED** respectively, not commercial releases. End-user physical-device testing has not been established. Publisher release approval and private production certificates remain empty/external.
- Next scope: user may install and evaluate the two new native previews and PWA appearance; perform focused UI polish based on actual feedback, then production publisher/release onboarding in separately authorized engineering work. Preserve signed-release and OS-consent boundaries in every change.

## Accepted owner-ready WinGet lifecycle, offline hashes and trusted main runner — RUN19 (2026-11-05)

PR #88 merged main `6acf4297393d5685da2bd0def474befcf9300fc1` after exact-head `2ba38498477385449567fffb8cbfcab4c9f6b6af` passed **5/5 relevant hosted workflows**: CI #41914613684, CodeQL #41914614831, supply-chain #41914614082, Android+Windows owner preview packaging #41914613853 and native Windows installer lifecycle #41914615049. See `docs/OWNER-READY-GAP-LEDGER-2026-11-05.md`.
- Windows WinGet Explorer now offers **local installed package inventory** (source-pinned temporary export), and **explicit user-confirmed uninstall** of an exact previously inspected package. After a 0 CLI exit, inventory must independently show the package missing. Upgrades require independently observed newer version. No silent elevation/EULA acceptance, arbitrary code execution, approval of owner-catalog binaries or upstream installer reimplementation.
- Windows and Android owner preview ZIPs now contain `HamApp-Verify-Preview.cmd`, a read-only local SHA256/manifest verifier. Actual hosted Windows CI confirmed good EXE/NSIS and rejected modified EXE, no installation. Current downloads: Android artifact #13363542959, Windows artifact #13364660881, both run #41914613853, 7-day retention.
- `.github/workflows/windows-qa.yml` expanded to Windows source paths with **self-hosted [Windows, X64, hamapp-windows], trusted-main-only**, serialized. It runs Python source tests, offline site build and read-only WinGet version diagnostics; no public PR, no package installation and no local inventory disclosure. **Actual owner runner availability/allocation/outcome is NOT independently verified** by the connector; queued is NOT PASS. Review the main branch's owner QA Actions.
- The debug Android APK and unsigned Windows EXE/NSIS are for owner tests, not production. Genuine publisher approvals, stable offline signing key+backup, real signed F-Droid HTTPS origin, Windows Authenticode identity and physical-device verification remain separate external requirements.

## Owner directive — do not ask for manual GitHub Actions clicks (2026-11-06)

For routine, previously authorized repository work, **do not instruct the owner to switch to `main`, open Actions, and click `Run workflow`**. Instead:
- Reuse the existing project's own self-hosted runner and main-branch automatic `push` workflow when safe; or use the connected GitHub API to post the exact owner-only issue comment supported by the repository. Build, run, read real logs, and return actual artifacts where authorized.
- If only a manual `workflow_dispatch` exists, and no available connector can dispatch it, add a narrowly scoped, owner-authenticated `issue_comment` route to the *same reviewed workflow* where safe, then invoke that route via GitHub. Do not create a new runner, VM, Work/Codex dependency, duplicate build pipeline or unrestricted shell bridge. Preserve the repository's existing constraints, workflow isolation and code-first delivery goals.
- Never automatically execute unreviewed PR code on the permanent Windows host; never auto-approve higher-impact installations, production deployment, network/security changes, signing secrets, paid calls or external account access. Such work retains the exact-SHA and consent gates already specified elsewhere. A mere chat request for automation does not waive those gates.
- A queued or accepted GitHub run is **not** a successful build. Check real jobs and outputs. Keep product implementation and delivery as the goal; do not generate repeated probes when a reviewed build can proceed.

This is a workflow usability policy, not a blanket privilege or host-operation authorization.

<!-- BEGIN OWNER_RUNNER_FABRIC_MANAGED_V1 -->
## GLOBAL DEFAULT — Owner Runner Fabric / استاندارد دائمی تمام مخزن‌ها

این مخزن تحت استاندارد مرکزی Runner Fabric حساب rezamahrm100-ops است.
برای کارهای GitHub Actions، Build، Sandbox، Runner یا Release، مرجع زنده:

https://github.com/rezamahrm100-ops/windows-command-center/blob/main/docs/OWNER_ISOLATED_EXECUTION_STANDARD_FA.md
https://github.com/rezamahrm100-ops/windows-command-center/blob/main/docs/RUNNER_FLEET_RELEASE_STANDARD_FA.md

قواعد دائمی:
- هر مخزن ثبت رانر اختصاصی، مسیر کار، کش و خروجی مستقل خودش را داشته باشد.
- انتشار private Release از Artifact تأییدشده منتظر Windows Sandbox نماند.
- Build روی میزبان فقط با SHA و اسکریپت/وابستگی بازبینی‌شده و مجوز مربوط؛
  BUILD-ONLY به‌تنهایی دلیل امن بودن نیست.
- کد PR نامطمئن و آزمون بومی/GUI آن فقط در محیط ایزولهٔ معتبر اجرا شود.
- هر job استفاده‌کننده از Windows Sandbox، کتابخانهٔ همگام‌شدهٔ
  .github/owner-runner-fabric/Owner-SandboxLease.ps1 را در همان فرایند
  PowerShell اجرا کند و تا پایان عمر مهمان قفل مشترک را نگه دارد.
- Sandbox ناشناس/متعلق به پروژهٔ دیگر هرگز stop/attach/kill/reset نشود.
  فقط فعالیت وابسته به مهمان به تعویق بیفتد.
- این بند و کتابخانه توسط WICC خودکار و فقط در مسیرهای مدیریت‌شده همگام
  می‌شوند. آن‌ها را جداگانه در هر پروژه بازنویسی نکن.
- نصب روی دستگاه مالک، UAC، تغییر سیاست‌های امنیتی و اسرار تولیدی
  نیازمند مجوز مستقل هستند؛ خودکارسازی گیت ایمنی را دور نمی‌زند.
- این متن به‌تنهایی workflow فعلی را امن یا مجهز به قفل نمی‌کند؛
  workflow مهمان باید کتابخانه را واقعاً فراخوانی کند.
- قواعد اختصاصی پروژه بدون تعارض با ایمنی و هویت رانر محفوظ‌اند.

مخزن تازه با فهرست زندهٔ GitHub شناسایی می‌شود و در اجرای بعدی
کنترل‌گر WICC این بند و کتابخانه را دریافت می‌کند؛ اگر اجازهٔ
نوشتن در شاخهٔ اصلی وجود نداشته باشد، مانع گزارش می‌شود و
Branch Protection به‌طور خودکار تضعیف نمی‌شود.
<!-- END OWNER_RUNNER_FABRIC_MANAGED_V1 -->
