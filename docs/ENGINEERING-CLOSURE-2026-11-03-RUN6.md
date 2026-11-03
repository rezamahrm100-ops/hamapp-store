# HamApp integrated engineering execution RUN6 — 2026-11-03

## Immutable accepted Android native change

PR [#55](https://github.com/rezamahrm100-ops/hamapp-store/pull/55) merged into main as `30f863579e290bffa78f4ffe59726605296f30d6`. Feature head was `57ede25f5a576f8852d9dcb0523e1afa8ae7afbe`.

The native Android app now hands an independently approved F-Droid repo URL + fingerprint to the installed **official** app via an explicit `fdroidrepos://` ACTION_VIEW targeted at `org.fdroid.fdroid`, preserving owner review, Android user consent and disabled install controls when no repo is independently approved.

**Genuine GitHub-hosted upstream integration**: download official F-Droid APK + detached signature; require the independently pinned public F-Droid GPG primary fingerprint and genuine cryptographic signature; verify Android APK developer certificate SHA256 and official package via `apksigner`/`aapt`; install on Android 35 emulator, launch official app, dispatch a deep-link intent, prove official process survives and record real screenshot. The dummy `example.invalid` test URI is NOT added as a repo.

- Real [signed official APK/intent emulator #41595096805](https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41595096805) **SUCCESS** on final PR head; log explicitly says `UI_DUMP_VERIFIED=false` due upstream UIAutomator null root, not a passed accessibility/UI audit.
- PR final-head [hosted Linux/Windows CI #41595096716](https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41595096716), [CodeQL #41595096780](https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41595096780), [Trivy #41595096844](https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41595096844), [Android debug APK #41595096717](https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41595096717), [real ClamAV debug APK #41595096929](https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41595096929), [Android UI smoke #41595096748](https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41595096748), [Android v1-v2 DEBUG upgrade #41595096736](https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41595096736) all **SUCCESS**.
- On main `30f863579e290bffa78f4ffe59726605296f30d6`, **eleven** hosted CI, CodeQL, Trivy, F-Droid real signed-index test, official F-Droid client intent, native APK, Android emulator, debug two-version, ClamAV, Pages and reproducible evidence jobs all **SUCCESS**. Owner self-hosted Windows QA [#41595556568](https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41595556568) was **QUEUED**, NOT PASS.

## Windows native Authenticode engineering candidate (not accepted unless explicitly reconciled below)

PR [#56](https://github.com/rezamahrm100-ops/hamapp-store/pull/56), branch `feature/hosted-authenticode-real-signing-drill-20261103`, introduces a real hosted-Windows test: two separately signed actual PyInstaller EXE copies with disposable local identities, genuine Windows OS Authenticode readback, wrong/unsigned/tampered signer refusal, no binary or signing key uploaded, original preview remaining unsigned. **Do not record a merge or acceptance until exact final source head checks actually pass.**

Initial PowerShell `New-SelfSignedCertificate` on GitHub-hosted Windows blocked in certificate creation, running over eight minutes before a genuine step timeout; no signing success at that head. The newer test uses built-in .NET in-memory `CertificateRequest.CreateSelfSigned` with code-signing EKU, then genuine `Set-AuthenticodeSignature` and native `Get-AuthenticodeSignature`. Current accepted feature source gate outcomes at provisional head `2c74aaffc5bbab0ba62bf51e1836aa092b759749`: CI, CodeQL and Trivy **SUCCESS**; real Windows EXE signing workflow [#41595938305](https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41595938305) **IN PROGRESS** at this writing. If the hosted test fails, inspect diagnostics, repair, rerun; do NOT merge on source tests alone.

## Remaining genuine engineering and independent owner gates

- **Production Android**: actual stable owner repo signing key, independent encrypted off-machine backup, independently owner-approved fingerprint/origin, verified signed index-v2 on real HTTPS, official F-Droid client **subscription**, package install and two genuine releases update/rollback, signed app release, real device consent. Current official-client test is intent-only; it did NOT add or synchronize any repo and did NOT install an app from F-Droid.
- **Production Windows**: genuine approved Authenticode certificate/key, signed Windows installer or MSIX, publisher-verified WinGet mapping, consented interactive GUI UAC install/update/rollback and device acceptance. Hosted disposable self-signed signatures are NEVER proof of a production developer certificate.
- **Publisher backend**: owner-local token-authenticated quarantine exists; remote production publisher identities, MFA, tenant isolation, encrypted storage, abuse controls, moderation, payment workflows and production deployment are still engineerable/open.
- **Release approval**: private first-party candidate, authentic producer attestation, developer certificate, malware/dynamic behavior/license/privacy review, real signed public packages and owner-reviewed promotion. Public trust registries and download links remain deliberately EMPTY.
- **GitHub ruleset**: Issue [#31](https://github.com/rezamahrm100-ops/hamapp-store/issues/31) still needs enforceable owner-admin main branch protection; CODEOWNERS metadata is not a protection rule. Connected GitHub tools do not expose this admin modification.
- **Owner Windows QA**: queued jobs are not a successful test; never run unreviewed PR code on the trusted self-hosted owner runner.

**Final verdict at this checkpoint: ENGINEERING PARTIAL; PRODUCTION NOT APPROVED.** No owner secrets, release binaries, real publisher identities or production signing materials have been uploaded to public GitHub.

## Next execution contract

Read current `main` SHA, `AGENTS.md`, root + docs `NEXT-EXECUTION.md` and this ledger; reconcile latest exact live checks. Finish any still-open reviewable Windows Authenticode PR only after **real** Windows hosted acceptance. Advance a genuine disposable official F-Droid **client subscription/update** in safe isolated emulator (not another signed-index-only fixture), plus auth/tenant/release-governance code where feasible. Keep production approval, private owner key custody/physical installation and admin branch ruleset separate, explicit and unclaimed. Use all free hosted GitHub CI and existing upstream software; do not stop at a superficial status or replicate accepted Android work.
