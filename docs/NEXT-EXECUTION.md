# HamApp — next integrated execution contract

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
