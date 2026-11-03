# HamApp — next integrated execution contract

## OVERRIDING EXECUTION PRIORITY — all feasible engineering in one integrated run (effective 2026-11-02)

The owner has explicitly changed the goal: **stop optimizing for the next microfix, incremental paper gate, or status-only reply. Optimize for closure of the entire technically actionable backlog in one coordinated run.** The controlling document is **[ONE-RUN-TECHNICAL-CLOSURE.md](ONE-RUN-TECHNICAL-CLOSURE.md)**. Read it first and use its complete workstream inventory, acceptance matrix and end-state contract.

Older sections below describe historical continuation stages; they **do not authorize stopping after one stage**. Run as many dependent and independent workstreams as feasible in the same turn, creating several reviewable PRs if needed and merging only after actual relevant tests. Distinguish technically unfinished work from genuine outside gates (private owner-held signing keys, independently approved issuer/trust origins, real-device consent, service accounts, unavailable admin API). No fabricated production completion or security shortcuts; leave no engineerable gap untouched merely because some production approvals are external.


**Start from AGENTS.md and ENGINEERING-STATE.md. Verify live main, workflows, open PRs and issues.** Do not substitute this text for current GitHub data.

## Mission: finish as much independent engineering as possible in a cohesive run

### Tranche A: source identity and publication provenance (highest priority)
1. Inventory existing authorized source repositories and their verified release assets privately, without exposing private names/files in this public repo.
2. Build a machine-checkable allowlist of official source repo IDs, immutable release tags, exact asset digests and expected publisher cert identities. Do not register any signer from an untrusted APK or invented data.
3. Extend existing offline publisher gate with independently verified GitHub attestation check (gh attestation verify), source SHA identity and malware/permission scan. No claims based only on a source_sha string or fabricated receipt.
4. Create a protected owner-reviewed release promotion transaction: verified signed files, signed metadata, atomic catalogue update, revoked release rollback handling, auditable approval. Public download buttons must remain disabled until all gates pass.
5. Implement separately trusted WEB deployment origin approval before enabling `status: released` for `web` apps.

### Tranche B: native distribution (reuse upstream, do not build package tools from scratch)
1. Evaluate pinned F-Droid upstream client revision/build, license and trademark compliance. Prepare and test a properly branded Android client that can subscribe to a trusted signed repository. Android installation must honor OS prompts.
2. Integrate fdroidserver in an isolated private signer environment with persistent repo signing keys, independent backups, index verification, and public HTTPS publishing only after approved release evidence.
3. Use Windows Package Manager / winget / MSIX / Authenticode where applicable for a native Windows catalogue/install/update assistant, with explicit user approval for privileged operations and anti-downgrade rules.
4. Run Linux/Windows hosted checks first; self-hosted Windows runner only for code from trusted main. Use emulator/isolated devices for update continuity.

### Tranche C: front end, publisher workflow and acceptance
1. Reuse tested open-source UI components where licensed and beneficial, but keep RTL performance and accessibility. Build app details, changelog, provenance badges and verified link disclosure, without invented downloads or popularity statistics.
2. Start publisher operation via GitHub PR-based review and minimal audit logs; add backend/accounts only for actual access control needs. Do not put private publisher/source information in public JSON.
3. Test signed two-version Android and Windows installs, incorrect certificate, corruption, compromised/revoked signer, downgrade, offline restoration and failure recovery. Preserve signed index and trust root continuity.
4. Keep one cohesive, reviewable PR per independent release/installation workstream. Gate on hosted Linux + hosted Windows + CodeQL and inspect actual published artifacts. Production release needs genuine device and signer acceptance.

## Execution discipline
- Prefer GitHub Free public Actions, hosted runners, short-lived artifacts, attestation verification, standard package tools, maintained open-source upstream code, explicit pinned versions and licenses.
- Never run unreviewed PR code on owner Windows. Never upload private signing keys or unreviewed app binaries to this public repo.
- Update AGENTS.md and ENGINEERING-STATE.md after the batch with immutable SHAs/run links, exact acceptance gates and blockers.
- Avoid requesting manual tasks unless an unavoidable owner signing/authorization/device gate remains. Do not announce completion without actual evidence.

## Windows-client follow-up (after preview PR acceptance)
- Inspect `.github/workflows/windows-client-preview.yml` for a successful hosted Windows EXE artifact. It remains UNSIGNED and nonproduction.
- Add approved app-to-winget mapping only after independent owner review of package ID, signing identity, source provenance and exact version continuity; no invented publisher registrations.
- Complete publisher-controlled offline Windows EXE signing, installer/update validation on real interactive desktop and native GUI smoke tests. Do not run unreviewed PR EXE on owner runner.
- Prioritize similarly upstream-based native Android client work via F-Droid client evaluation and signed repo, rather than rolling a new package manager.

## Continuation after verified Windows preview PR #15

1. Inspect live `main` and recheck https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41484699926 to establish which unsigned preview artifact was actually built. It is not a signed release.
2. Native Android client is the next high-impact code workstream: reuse a pinned upstream F-Droid client implementation with GPL source and trademark compliance; build an independent APK in hosted CI, test signed F-Droid repository registration, and do not claim production install without keys and device QA.
3. For Windows, independently verify a real publisher package, winget ID, version and binary signer. Preserve empty mapping until verified. Provide a secure signing environment outside public CI, sign and version the desktop EXE, run interactive owner-device install/update QA only under explicit owner approval, then publish a properly signed release.
4. Build authentic release source provenance and owner-reviewed promotion (certificate continuity, malware policy, anti-rollback, verified GitHub attestations) before enabling downloads.
5. Improve real application detail pages/accessibility and publisher governance via safe GitHub PR workflow; do not build a new install system where F-Droid/winget already provide one.

## After Android native preview verification
- Inspect `.github/workflows/android-client-preview.yml` actual run + APK digest. Verify Android Studio/Gradle compatibility and manifest; perform emulator or instrumented UI smoke tests in isolated CI.
- Add independent F-Droid signed index verification, pinned repository key fingerprint and stable private signer backup in trusted environment before enabling any production Android package install flow. Do not infer validity from public JSON alone.
- Explore F-Droid's reusable client libraries under their applicable GPL licenses if a tightly integrated installer is needed. Existing native code currently hands off to the separate official client, not an embedded package manager.
- Continue release source-to-binary provenance and Android release-key continuity, then two-version real-device update acceptance. Never register the ephemeral Android debug signing key.

## After hosted Android emulator acceptance
- Review a real GitHub Android emulator workflow run: APK installation into ephemeral emulator, app activity start, UI dump, disabled F-Droid handoff and screenshot. A green emulator test is not equivalent to signed repo subscription or physical-device two-version APK update acceptance.
- Prioritize real signed F-Droid repo with persistent offline key / verified index and an owner-approved signer registration, then active install+upgrade on isolated device and stable APK release signing.

## Next integrated batch after verified Android native/emulator PRs #17 and #18

1. Verify GitHub main SHA and status of the six main workflows after PR #18; confirm actual Android Debug APK and emulator screenshot artifacts before claiming green.
2. Move toward a **real signed F-Droid repository and first eligible application**: check privately available owned release candidates, exact publisher certificate fingerprints and immutable binaries; get an independently trusted owner approval and signing key outside GitHub. Keep private source/release names out of this public catalogue until explicitly authorized.
3. Build an isolated, persistent-key fdroidserver signing workspace with verified official index and separate offline backup, actual QR/subscription smoke test, then publish signed metadata via appropriate HTTPS hosting (GitHub Pages is only a static project showcase under its terms).
4. Test F-Droid handoff on the Android emulator after a real signed repository fingerprint is approved, including two-version APK install/update, downgrade/revocation and persistence of signing keys.
5. Finish signed Windows client release and real winget/publisher provenance mapping; isolate owner-device/UAC acceptance from hosted CI. Do not activate download or install controls with synthetic data.
6. Review which F-Droid libraries or GPL-client code can be reused directly if integrated install/update UI is desired; follow GPL source/notice/trademark obligations. The current native client uses the external F-Droid client as a companion, **not** an embedded F-Droid fork.
7. Update AGENTS.md and ENGINEERING-STATE.md with exact accepted SHA and runs after each coherent branch, not with guesses.

## Next after native artifact provenance acceptance
- Verify both trusted-main native build attestation jobs, their exact SHAs and review receipts from GitHub Actions.
- Build private, independently approved source/release intake: require exact producing repo ID, signed binary digest, developer certificate pin, independent source provenance and malware policy before enabling ANY download.
- Use existing fdroidserver for stable-key signed repository, verify signed index against pinned fingerprint, then test two consecutive versions in isolated Android emulator and owner-controlled device. No private key in public CI.
- Windows production EXE needs owner-signed Authenticode and independent real install/update acceptance. Neither a GitHub attestation nor a preview EXE substitutes for it.

## After accepted GitHub native attestations + F-Droid index policy
- Verify live main and new preflight PR checks; keep `catalog/android_repository.json` null until independently approved F-Droid signing key and public HTTPS origin actually exist.
- Perform official fdroidserver signed-index-v2 verification against a pinned external trust root using scripts/verify_fdroid_signed_index.py; its current tests are mocked and cannot prove a real deployed repo.
- Establish persistent offline F-Droid keystore with backup and independent owner-controlled signing environment; do not generate ephemeral fake production keys in public CI.
- Verify an actual eligible owned app's producer GitHub provenance, signer certificate identity, release digest and approval **privately** before any public catalogue entry; stage/index/install/update two real versions on isolated emulator, and preserve rollback/rotation controls.
- Sign the native Android APK and Windows EXE using stable owner-approved production release signing identities, then run real device install/update acceptance. Until then NO public download or installation claim.

## Next coherent execution (after accepted PR #20/#21)
1. Inspect live GitHub main and all green checks. Prefer completing actual signed-repo builder/validation in an isolated non-public signer workspace using upstream fdroidserver, durable owner key and out-of-band fingerprint confirmation. Never upload a signing key to a public repo/Actions artifact.
2. Run scripts/verify_fdroid_signed_index.py against a genuine owner-approved HTTPS index-v2 with independently pinned URL+fingerprint; mock tests do not count. Then verify F-Droid client subscription on an emulator/device, unsigned/bad key rejection, and two signed app versions/upgrades.
3. Identify one eligible owned app from authorized repositories, privately verify source attestation, signed APK/EXE publisher certificate and exact version hash. Request only genuinely necessary owner release approval. Do not publicize private app names or QA binaries prematurely.
4. Complete production code signing and real device installation acceptance for Android/Windows clients, then enable approved catalog metadata atomically. No public download until all gates pass.
5. Continue with upstream F-Droid/winget rather than writing another installer. Keep AGENTS and ENGINEERING-STATE updated with exact workflow URLs and real acceptance gaps.

## After successful F-Droid disposable signed-index integration drill
- Verify the real GitHub signed-index drill's exact main SHA/run and receipt. Distinguish this end-to-end test of a disposable key from owner-approved real signer acceptance.
- Next engineering: build a safe private owner-controlled, durable signing workspace with isolated backup and signed-index verification against independently pinned public trust. No unsigned fallback, no owner signing keys in GitHub.
- Select one eligible privately owned app, verify real production signer, GitHub source provenance, immutable release digests and version continuity; then test two genuine signed versions/install/update on emulator. All approvals stay disabled until independently grounded evidence.

## After native Android debug two-version upgrade acceptance
- Inspect exact hosted Android two-version workflow SHA/receipt, confirm default downgrade refusal and native UI remained fail-closed. Do NOT confuse test debug signing with real production app/F-Droid update.
- Next run a true F-Droid **client** install/update using owner-approved signed repository and two publisher-approved APK versions with stable signatures in isolated emulator, then accept owner device only with permission.
- The ephemeral signed-index drill succeeded on main run #41497810315; document its acceptance and keep production signing keys outside public CI.

## After Android signer-mismatch/corrupt-package QA
- Inspect the actual `android-two-version-smoke.yml` run for branch `feature/android-package-rejection-qa-20261102`. Require Linux/Windows hosted CI + CodeQL + emulator job success and the safe evidence artifact before merging.
- Confirm on-emulator refusal of downgrade, foreign signer and truncated APK, with versionCode=2 still installed. These are **debug** tests, not publisher-signed F-Droid adoption.
- Remaining independent engineering prioritization: owner-controlled persistent repo signing + offline backup, an independently approved origin/fingerprint, first eligible source/release provenance with real publisher certificate, trusted F-Droid client two-version update, and production signed Windows installer acceptance. Never register test identities.


## Next after accepted PRs #27–#29 (2026-11-02 consolidated priority)
1. Inspect live main at/after `eb08797a42fdde5cfacd0f6542ee0100d02bb680`; recheck terminal outcomes of main workflows #41505611808 (CI), #41505612155 (CodeQL), #41505612176 (trusted owner Windows QA), #41505612008 (Android preview), #41505612132 (Windows preview), #41505611948 (Pages), #41505612012 (site evidence). Treat pending as pending, never as success.
2. **Actual production trust instead of more simulated gates**: privately identify and authorize ONE eligible first-party app release; independently check publisher certificate, exact immutable binary digest, upstream build/GitHub attestation and source SHA. Keep private project names/assets out of this public repository until explicit publication approval.
3. Establish a persistent owner-controlled F-Droid keystore and independently verified offline backup outside public CI and repo. Register the genuine fingerprint through owner review; produce/deploy a signed v2 index at an approved HTTPS origin and verify it from an independent trust pin.
4. Exercise the official F-Droid Android client subscription, two genuine signed versions/install/update, wrong signer, corrupt package, downgrade, key continuity and restoration in an isolated device. Existing debug APK Android 35 QA is accepted but NOT this production acceptance.
5. For Windows, use official winget/MSIX/Authenticode and exact publisher mapping; sign production EXE with approved certificate and perform real interactive installation/update with explicit owner/device approval. Do not allow a public PR to run on owner Windows.
6. Independently verify exact deployed immutable web content and redirect/TLS/provenance details before filling either empty web trust registry. The new metadata guard alone does NOT validate live bytes.
7. Only after genuine release gates and any legally necessary authorization, atomically promote an approved catalogue entry; no fake releases or automatic paid marketplace/portal rollout. Continue truly unfinished source provenance, publisher review, portal/access and UI work via small independently reviewable secure PRs.
8. Keep root NEXT-EXECUTION.md, AGENTS.md and ENGINEERING-STATE.md current with exact SHAs and workflow outcomes. Prefer GitHub-hosted tools and reused upstream software; ask the owner ONLY for actual key custody, private release authorization, or consented physical-device actions.

## Current integrated cross-platform batch
- Validate actual CI/CodeQL/Android/Windows results on `feature/integrated-technical-closure-20261102`. Check that the web offline snapshot never carries released binaries, a Windows operator sees only WinGet completion rather than fake install success, and production provenance requires a real pinned `gh attestation verify`.
- After merging, finish remaining tasks in `docs/INTEGRATED-GAP-MATRIX.md` as far as real tools permit. Do not claim whole-project engineering PASS while a real technical gap remains.

## Owner-controlled signing workspace (engineering, not owner commissioning)
- Review/accept scripts/fdroid_key_custody.py and docs/FDROID-KEY-CUSTODY.md only after green source tests; real owner key never enters public CI, tests use local dummy bytes and simulated different volumes. Actual persistent key generation/storage, encrypted separate offline medium, restore/sign test and independently pinned F-Droid public index remain unresolved external real-world gates.

## WinGet postcondition gate
- Verify exact hosted acceptance of windows_client/installed_state.py and Windows GUI: official WinGet export JSON pre/post operation, no downgrade on installed version, no false success on mismatched version, no private device data upload. Complete actual owner-approved package mapping/signature and consented install/update when genuine provenance and permissions exist. Production Windows signing and all other gaps remain.

## Browser PWA acceptance
- Verify `tests/browser_pwa_smoke.mjs` truly runs Chromium (not source-only checks), with native dialog, search, platform filters, service-worker offline reload and no fake download controls. Review workflow/CI result and safe screenshot before merging. Full screen-reader and real-device audits remain separate.

## Post integrated PRs #33–#37: concrete continuation
- Source of dated actual results: [ENGINEERING-CLOSURE-2026-11-02.md](ENGINEERING-CLOSURE-2026-11-02.md). Main SHA `8a76c419e581506d395e9eb6e016425d9afa2ca1` and six main workflows all succeeded. Real Chromium finally passed after fixing Service Worker `window.isSecureContext` for 127.0.0.1.
- **Next mission** is not repeating completed PWA, WinGet readback or dummy-key tests. Build the owner-reviewed atomic promotion/revocation review workflow, real upstream software supply-chain/malware/permissions/SBOM review, actual trusted F-Droid client signed-index subscription and production-version tests when genuine owner key/origin available, production Windows Authenticode/device install when owner approves, and publisher portal/access-control architecture if requirements warrant it.
- Preserve separate external gates, no publisher or installer metadata fabricated; verify live main and any open Dependabot PRs and Issue #31 security ruleset before merging unreviewed automation. Keep engineering verdict PARTIAL unless all requested technical tasks genuinely pass.

## Owner-governed release transactions and scanning
- Confirm actual CI and security scanner run for `feature/secure-release-governance-and-supply-chain-20261102`. PR-only release/signing-key revocation proposals must disable any active download links and validate both JSON records together; no direct public deploy or unaudited owner approval. Audit SHA-256 before/after; require a GitHub single-commit change after independent review.
- Source filesystem Trivy vuln/secret/config scan and CycloneDX metadata alone do not clear release APK/EXE for malware, license/privacy or Authenticode, and no production binary is approved. Resolve branch-ruleset Issue #31 via authorized admin only.

## Android third-party permission and publisher acceptance
- Check the actual Android native preview workflow's official `aapt` manifest permission scan and debug receipt after PR merge. In approved private-publisher intake, use independently reviewed per-app allowed permission policies and inspect real APK bytes, then combine with true OS signature, provenance, scanner, real signed F-Droid index and on-device install/update. Preview permission scan is not malware clearance.

## Mobile PWA a11y real-browser continuation
- Inspect exact hosted Playwright + axe CI job, assert serious/critical WCAG2.1 A/AA rules passed for dark/light/modal and no mobile horizontal overflow. If red, fix actual UI issues, not skip the gate. Real screen reader, device and broader WCAG acceptance still require independent evidence.

## Second integrated closing pass (2026-11-02)
- `docs/ENGINEERING-CLOSURE-2026-11-02-RUN2.md` is the latest dated ledger, not live evidence. It records six merged PRs and exact Actions URLs: emergency review-only release/signer revocation plans + source Trivy/CycloneDX; actual aapt Android debug permission audit; live mobile Chromium axe with brand/contrast fixes; official Pages and checkout action upgrades. Verify all latest main workflows, particularly emulator/F-Droid drills, before relying on main acceptance. Continue unfinished genuine engineering in one integrated execution; production signatures/keys, approved release and physical-device evidence remain real owner/external gates.

## Owner candidate intake and byte-level archive audit — 2026-11-03
- Owner-local preflight must match actual file digest, OS signer, pinned GitHub attestation and Android aapt permission policy; run ZIP CRC/traversal/expansion checks on real APK and final artifact rehash. The public CI runs only a genuine first-party debug APK, which is **not** production release approval. Check live main QA after merge. Continue actual malware/dynamic analysis, identity registration, signed repo client and owner-device acceptance, with branch protection still independently required.

## Binary antivirus signature gate
- Check docs/ACTUAL-ANTIVIRUS-SCREENING.md and latest hosted actual APK ClamAV/freshclam DB receipt; owner local signed candidate intake now requires fresh clamscan on identical immutable bytes, refuses scanner absence/detections/TOCTOU, and never approves public release. Independently clear dynamic behavior and real publisher rights.

## Actual verified final 2026-11-03 engineering handoff
- `docs/ENGINEERING-CLOSURE-2026-11-03.md` supersedes stale work-in-progress sections: PRs #43/#44/#45 merged and all eight exact-main `e11f32ae3773e7b5488545230a1e96e27ed8dae4` workflow conclusions SUCCESS. Native real APK ZIP/CRC and ClamAV fresh-signature test accepted only for first-party DEBUG artifact. Public Pages real HTTPS byte parity accepted for first-party storefront, not app web origins. Still outstanding genuine production certificate/key/index/F-Droid client, Windows authenticode/device acceptance, private publisher submission roles and admin branch ruleset. Focus these instead of mock/duplicate checks.

## Private untrusted publisher submissions
- Read `docs/PRIVATE-PUBLISHER-QUARANTINE.md`, inspect exact CI for real POSIX disk isolation, actual byte copy/hash, validation, event quarantine/rejection and owner local crypto-check integration. Native Windows scanner must run on an authorized Windows session on same hash; private POSIX inbox alone is not Authenticode. Full authenticated private tenant submission service, owner approval and encrypted production storage are still unimplemented.

## Actual F-Droid staging integration security boundary
- `fdroid_bridge.py` previously accepted signer/size alone. Verify new staging gate requiring full `owner_candidate_intake.assess` source-to-actual-package plus archive+permission+fresh antivirus results before invoking upstream `fdroid update`, with exact SHA recopy and private 0700/0600 signing workspace. Never claim synthetic CI tests are real producer attestation/production signed index. See `docs/FDROID-STRICT-VERIFIED-STAGING.md`.

## Signed F-Droid index-v2 / APK byte binding
- Verify `fdroid_bridge.py` now refuses staging completion without real signature verification of private `entry.jar`, owner-pinned repo fingerprint, signed index-v2 sha256/size and exact candidate package/versionCode/versionName/SHA. On mismatch it removes new APK and creates a BLOCKING marker; do not claim a changed signed index was rolled back. Hosted disposable F-Droid real signature drill must pass at PR SHA. Still no production owner key or client install.

## 2026-11-03 private publisher & F-Droid full workstream handoff
- Exact ledger `docs/ENGINEERING-CLOSURE-2026-11-03-RUN4.md`. Main SHA `562d4cd808a73e11a139ab52f5ee4adbe50ef107`, PRs #47/#48/#49 verified merged. Six of seven listed current-main workflows SUCCESS; self-hosted owner Windows QA #41587826538 QUEUED on 2026-11-03 inspection. Do not conflate CI disposable F-Droid keystore with a real owner production signing root. Future code: authentic private publisher submission/authorization and immutable reviewed promotion, full Windows installer signature acceptance, real F-Droid HTTPS origin/client subscription and independently signed two-version install, branch ruleset admin. Keep all owner/private material outside public GitHub.

## Active next batch after actual integrated PRs #51–#53 (2026-11-03)
- Read `docs/ENGINEERING-CLOSURE-2026-11-03-RUN5.md` (exact SHAs, accepted hosted feature checks, post-main pending statuses, detailed remaining gaps). #51 local loopback authenticated publisher quarantine, #52 real two-debug-APK signed-index/actual APK file binding, #53 independent-volume ephemeral key-loss/restore/re-sign all passed real hosted source checks and merged. Continue other feasible engineering work in one cohesive run; do not reimplement these gates.
- Major independent next **integration**: approved signed repo and official F-Droid Android client genuine two-version subscription/install/update, with fail-closed invalid signer/revocation/corruption and evidence; production requires externally approved durable key/origin/first authentic publisher binary. Build safe disposable CI client tests as far as installed tools permit, never promote test keys.
- Other unfinished scope: full authenticated remote publisher platform/tenant controls, real promotion governance/protected GitHub main ruleset #31, Windows Authenticode/owner-approved winget mapping/real installer acceptance, product/privacy/malware behavior review and consented physical-device QA. No owner secrets or unreviewed PR builds on trusted runner. Verify latest main post-merge workflows before marking pass.

## Integrated 2026-11-03 RUN6 continuation — after official F-Droid Android accepted
- Canonical new source ledger `docs/ENGINEERING-CLOSURE-2026-11-03-RUN6.md`. PR #55 merged main SHA `30f863579e290bffa78f4ffe59726605296f30d6`, exact Android-hosted official APK GPG+signer verification/emulator installation/real `fdroidrepos://` dispatch accepted, all eight feature tests and eleven main hosted checks SUCCESS. **UI accessibility hierarchy remained unavailable** and its proof is recorded FALSE; no official F-Droid repository subscriptions, publisher signed app installs or updates.
- PR #56 is genuine Windows hosted signer engineering under review, NOT production signer; verify exact PR head native hosted Windows test success before merging. Early PowerShell New-SelfSignedCertificate blocked, replacement uses .NET CertificateRequest in-memory CodeSigningCert. Never call hung, failed or queued jobs green.
- Next independent high priority: true official F-Droid client trusted signed repo addition/refresh, two-version actual APK install/update in isolated emulator with no owner production trust; private real owner-approved release/source identity; production Windows Authenticode/WinGet mapping/consented device acceptance; authenticated publisher service/tenant isolation; enforce main ruleset Issue #31. Preserve no-release policy until proven real gates.

## Active RUN7 continuation — accepted real Windows PE portable Authenticode (2026-11-03)
- **START HERE** `docs/ENGINEERING-CLOSURE-2026-11-03-RUN7.md`, live GitHub main and the whole-project closure contract. PR #56 merged into main `2cd503aa0247f73de960137ca45a4c85b21edf61`; real Windows-hosted EXE plus real two-certificate offline PE Authenticode positives/negatives on Ubuntu 24.04 succeeded #41611354053. Actual feature CI/CodeQL/Trivy and six hosted main workflow checks succeeded; owner trusted Windows #41611654981 still QUEUED.
- Native Windows cert-store attempts failed; accepted test is real cryptographic Authenticode **not Windows OS trust**. Test keys never published, real producer signer/public CA/SmartScreen/approved installer/WinGet/device QA still not accepted. Production NOT APPROVED.
- Next autonomous engineering batch: hosted isolated official F-Droid client **real signed repo enrollment/update via real APKs**, robust remote authenticated publisher tenant/review and release governance, production-compatible Windows MSIX/installer and winget acceptance code without real production secret, other gaps in the integrated matrix. Keep only genuine owner gates for public signer/publisher identity, physical device/install permission, repo live HTTPS, and admin ruleset #31. Reconcile final head/main CI and persist evidence; avoid microfix loops and duplicate accepted milestones.

## RUN8 integrated software continuation (2026-11-03)
- Canonical current ledger `docs/ENGINEERING-CLOSURE-2026-11-03-RUN8.md`; start with current live GitHub source SHAs/checks. PR #59 merged `33a18fcbe713cea5416bdd6f8b1f28ef12129b42`: real operator-private HTTPS TLS/CA/leaf-pin verified publisher transport and real POSIX exact-file quarantine; no verified legal developer identity/public deployment. PR #60 merged `c437292514504114f8852ebb49d0bb21c596ee32`: correct canonical native F-Droid scheme replacing HTTPS while keeping approved host/pin, eight hosted actual Android/official client gates PASS. PR #61 merged `c53f6f1403d5836882238a980003a4f517e4fdfc`: real **unsigned preview** NSIS installer v1/v2 installer-version upgrade, downgrade rejection, actual uninstall and registry cleanup on hosted Windows, exact native file digest; actual Android/Windows CI/CodeQL/Trivy and six main hosted checks SUCCESS. Owner Windows QA QUEUED, not accepted.
- PR #62 real upstream signed private v1/v2 repo + Android official client genuine HTTP requests, with signer private workspace outside served directory, is still in active review. Initial real signed `entry.jar` validation failed missing fdroid direct Python jarsigner config; same accepted fdroidserver initialization added. Generated metadata aux-files were then rejected by over-strict public mirror copier; now only approved extensions are mirrored, config/keys never copied. Reverify exact feature-head true emulator integration SUCCESS before merge; never misreport F-Droid in-client APK installation or real production signing.
- Next whole-project technical closure: official F-Droid real signed repo subscription/install/update, verified publisher MFA/account/tenant moderation and release approval, Windows production signer/MSIX/WinGet and real distinct app upgrade/rollback, official owner-device acceptance and admin protected-main ruleset #31. Preserve empty trust registries, HTTPS public origin permission and no binary downloads.

## RUN9 actual integrated execution contract (2026-11-03)
- Canonical source/evidence `docs/ENGINEERING-CLOSURE-2026-11-03-RUN9.md`. Three actual accepted PRs: #64 token rotation/revocation enforced live in HTTPS/HTTP, #62 genuine official F-Droid Android client's real signed v1/v2 HTTPS index fetch, #65 real Windows installer lifecycle with two separately compiled different native EXEs. Exact merge main `e8bb47027087d63bd0f9cb467011b393dbd7a98b`; six hosted workflow checks SUCCESS, trusted owner Windows QA #41623437229 QUEUED; no protected main ruleset.
- Check genuine open PR #66 after each head change for actual Android SQLite repo persistence, not just source/mock or network requests. Current accepted F-Droid status is network-fetch ONLY; native F-Droid DB registration, its own app v1 install/update v2 and persistent trusted repo signer pin NOT accepted. Production HTTPS repo signer and app signer are owner-controlled keys not CI credentials.
- Continue integrated software implementation/test/merge for any remaining release/publisher account/WinGet/F-Droid app installation scopes; distinct genuine owner gates are physical device/UAC permission, real legally verified developer identity, approved persistent release signers and private offline backup, live HTTPS origin and GitHub admin Issue #31. Preserve empty download trust registry.

## RUN12 latest verified facts and next real Android integration (2026-11-03)
- The older RUN9 text describing native F-Droid repo persistence and signer pin as missing is superseded: #66 SQLite host accepted; #71 official client **native CoreRepository.certificate SHA256 equals independently signed index JAR fingerprint** passed on real Android #41646828386 and merged main `892e75d1032c4791f3a241736d1bd2650109dfd5`. Source checks matched head SUCCESS. No official F-Droid in-client APK install or update has yet been accepted.
- Live PR #72 is the unaccepted genuine UI→HTTP APK GET→Android PM installed APK hash/cert/version 1 and 2 gate (Android #41648785901 initially in progress). If fails, retrieve full job evidence and inspect exact real UI; never replace real F-Droid install with `adb install` or auto-grant unknown-source permission just to go green. Separate owner trust roots/HTTPS/key backup, release moderation, protected-main Issue #31, physical owner installs remain open. [RUN12 ledger](ENGINEERING-CLOSURE-2026-11-03-RUN12.md).

## RUN13 current F-Droid consent and app installation engineering boundary
- PR #75 accepted: real exact-head signed indexes/native SQLite signer #41655629539 SUCCESS, merged `11e70a5633b308a97b71ecebea66b596f55655b4`. No generic early Add-repo click; only actual bounded dedicated Add-control action. Postmerge main real Android #41656844438 was active at initial report—verify outcome anew.
- PR #72 still open: Android #41654899145 failed **after** verified repo Add but with Android PM installed code absent, no stage-1 APK install. Latest diagnostic Android #41656738400 pending/in progress when written, exact first-tap screenshot and native log flags; never conflate a tap request with callback/installation. Main/handoff details `docs/ENGINEERING-CLOSURE-2026-11-03-RUN13.md`. All real owner signer/device/publisher approval and main Issue #31 remain open.

## RUN14 verified native Windows custom-root CA and exact Android sideload blocker (2026-11-03)
- Windows PR #77 integrated real disposable in-memory code-signing chain proof and wrong-root rejection, real hosted Windows #41660197319 SUCCESS, merged `34d4d0f06be5b6171bd8a39241fa78e708e34374`; no public CA trust or owner signing acceptance.
- F-Droid app PR #72 real #41659125811 downloaded v1 APK (GET count 1) and hit genuine Android 13 `F-Droid` install-from-this-source **OS blocking dialog**. Only on disposable hosted emulator the candidate exact OS Settings UI may be traversed with visible `F-Droid` `Allow from this source` and post-toggle UI verification. Current head `94f2872c0f09c321162fc4b6fb71c42de1ebddc2`, Android #41661386351 running at ledger time; source CI security pass; do not call installed until real native version 1 then version 2 and signer/APK bytes verified.
- Owner-only production/signing/device consent protected main Issue #31 unfulfilled. Read `docs/ENGINEERING-CLOSURE-2026-11-03-RUN14.md` and live exact SHA/actions before any merge.

## RUN15 real official F-Droid v1 proven, native repository v2 forced-update candidate
- Previous Android #41661386351 genuinely installed version 1 through on-screen F-Droid Android source settings and official-client APK GET with PM byte-for-byte SHA and signer readback. Job as a whole failed because post-v2 `fdroidrepos://` preview GET did not update saved package metadata; screen showed Open and no v2 client APK GET. No v2 claim.
- PR #72 latest `b71cc6fe79b0c530bf0f12af29a58cd441f47c8e` adds strict actual official F-Droid Repositories → exact disposable repo → Check for updates, not preview. Source CI/CodeQL/Trivy successful, real Android #41688263014 ongoing. Check live result, fix source if needed, merge only real full version 1→2 successful acceptance, verify postmerge main; no bypass or synthetic attestations. [RUN15 ledger](ENGINEERING-CLOSURE-2026-11-03-RUN15.md).

## OWNER-TEST DISTRIBUTION handoff — after RUN15
- User explicitly selected installer-first workflow: code/build/package, then owner handles physical install and testing. PR #80 merged main `4213d05f76a46417db135e487a4c7246d2dd3aba`. [Main actual native delivery #41696010045](https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41696010045) Android DEBUG signed .apk + Windows portable unsigned .exe + real unsigned per-user NSIS Setup SUCCESS. Both artifact packages include SHA256SUMS, a source SHA manifest, Persian README; 7-day retention. No extra functional acceptance inferred.
- Production/commercial app store is NOT done: approved third-party download links empty, real publisher identities/MFA/approval, Windows production CA signing/WinGet and production F-Droid origin/long-term signer, owner desktop Android/Windows acceptance, protected main #31 all separate gates; PR #72 upstream F-Droid v1→v2 client upgrade still unaccepted, not required to deliver owner preview binaries.
- Future code batches should start from owner test feedback, then implement remaining real engineering without redoing already accepted build work. Inspect actual latest main, artifacts, RUN15, [owner handoff](OWNER-INSTALL-TEST-HANDOFF-2026-11-03.md), and read the whole-project closure contract.
