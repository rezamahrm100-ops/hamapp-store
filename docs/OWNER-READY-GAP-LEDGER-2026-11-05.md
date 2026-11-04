# HamApp owner-ready gap closure and acceptance ledger — 2026-11-05

## Technical closure purpose

Usable owner preview, not a production-signed multi-publisher marketplace.
Build on accepted PRs #84/#86 (native Android Material 3 + separately installed
official F-Droid, native Windows ttkbootstrap + official WinGet, standalone
offline-capable Persian RTL PWA). No further package manager rewrite warranted.

| Workstream | Status in this tranche | Independent acceptance target | Nontechnical gate |
| --- | --- | --- | --- |
| Android native UI, browse and consent | Existing accepted | Gradle + emulator + official F-Droid intent + v1/v2 signed temporary repo | Device-owner consent |
| Android production distribution | Pending owner-supplied genuine release | Offline real publisher signature / index / fingerprint / origin | Durable offline keystore & backup, owner approvals |
| Windows public WinGet search/install/upgrade | Existing accepted | Hosted Windows unit suite and exact-source OS actions | User consent for each program |
| Windows installed inventory | Implemented / accepted on PR #88 | Temp-only official `winget export --source winget --include-versions`, exact-ID/Version parsing, privacy and tamper tests | Real user device acceptance |
| Windows interactive uninstall | Implemented / accepted on PR #88 | `winget uninstall --id X --exact --source winget --interactive`, user consent, independent installed-inventory absence after return | Real device, Windows UAC, software-specific remover |
| Windows commercial signing | Blocked (owner) | Real WinVerifyTrust and durable publisher identity | Authenticode certificate |
| Web/PWA offline and RTL UI | Existing accepted | Real Chromium dark/light/mobile WCAG and offline tests | Production hosting for commercial marketplace |
| Owner binary delivery | Upgraded / accepted on PR #88 | Hosted GitHub APK and EXE/NSIS, SHA256, one-click local checksum script; positive and corrupt-file negative Windows tests | Physical owner installs |
| Self-hosted owner Windows QA | Main-only workflow strengthened | Only `refs/heads/main`; WinGet version read-only; Python tests; no unreviewed PR binary on owner host | Runner registered, online, authorized user session |
| Publisher trust and reviews | Existing fail-closed engine | Signed source/cert/release continuity, anti-rollback and negative tests | First real eligible publisher, human review |
| Paid marketplace/backend/account | Not in installed personal-preview scope | Requires separate product/data/privacy architecture, not solved by cosmetic OSS | Hosting/domain, account owner decisions and operations |

## Trusted self-hosted runner boundary

`.github/workflows/windows-qa.yml` triggers on trusted main branch changes
to tests, scripts, Windows app source and installer definitions. It must never
trigger for pull requests, arbitrary fork commits or `pull_request_target`.
Its read-only `winget --version` diagnostics and offline Python suite do not
modify installed programs, upload local package inventories, change firewall,
VPN, network, privilege, remote access or owner files. All code must first
pass hosted PR checks, then be reviewed and merged to main.

GitHub runner **registration and online state are not asserted here**.
The post-merge main-only job must be checked for real allocation/results;
queued/not started is not PASS. Actions UI and logs are evidence.

## Practical owner flow

1. Download the latest **exact-head** GitHub Actions `HamApp-Android-Owner-Test-APK`
   or `HamApp-Windows-Owner-Test-EXE-Setup` ZIP (7-day retention).
2. Extract ZIP, optionally double-click `HamApp-Verify-Preview.cmd` on Windows
   to check manifest file names, sizes, SHA256SUMS and actual file hashes.
   **This is integrity only, NOT a trusted production signature**. This script
   performs no installation or downloads.
3. Open APK on Android with OS consent, or run unsigned Windows portable EXE/
   setup after owner validates origin and hashes. The native owner preview may
   be blocked by Windows SmartScreen or reject reinstall of Android with a
   different transient debug signing key; do not bypass unknown publisher
   warnings blindly, and back up any data before replacing older debug builds.
4. Android: open public F-Droid only with user consent, installation occurs in
   official F-Droid. Windows: discover software in WinGet, view installed
   packages, install/upgrade/uninstall strictly after exact-ID metadata and
   independent OS readback where possible.
5. Owner device findings (screenshots, specific failure, Windows version,
   Android model) are a separate acceptance step.

Upstream reference: Microsoft `winget uninstall` and `winget list` docs:
https://learn.microsoft.com/windows/package-manager/winget/uninstall
https://learn.microsoft.com/windows/package-manager/winget/list

## Verdict rule

PASS for exact-head hosted feature/packaging tests only when all relevant
workflows have actually completed successfully. Owner self-hosted main QA is
separate. Public production product acceptance remains PARTIAL until approved
publisher binaries, signing credentials, registered origins and owner device QA.
No synthetic signers or short-lived CI artifacts may be promoted as permanent
approved app downloads.

## Final RUN19 acceptance record (2026-11-05)

- Merged source PR: #88 https://github.com/rezamahrm100-ops/hamapp-store/pull/88
- Exact 5/5 accepted **hosted PR** workflow head:
  `2ba38498477385449567fffb8cbfcab4c9f6b6af`;
  main merged SHA `6acf4297393d5685da2bd0def474befcf9300fc1`.
  - Windows/Linux CI #41914613684 **SUCCESS**, includes the full Python test suite, Windows inventory, uninstall, approval separation and runner controls.
  - Source-supply-chain scan #41914614082 **SUCCESS**.
  - CodeQL #41914614831 **SUCCESS**.
  - Owner installable Android debug APK + Windows unsigned portable/NSIS + one-click integrity checker #41914613853 **SUCCESS**; Windows verifier genuine artifact accepted, corrupted EXE rejected in real PowerShell/CMD host.
  - Hosted real Windows EXE/NSIS install/upgrade/downgrade/uninstall and disposable Authenticode cryptographic/OS trust checks #41914615049 **SUCCESS**.
- Download short-lived (7 day) ZIPs:
  - Android debug APK and verifier: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41914613853/artifacts/13363542959
  - Windows portable EXE + unsigned NSIS Setup and verifier: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41914613853/artifacts/13364660881
- Run #41914613853 and #41914615049 certify **hosted** test builds and packaging only; real third-party WinGet app removal on owner's machine is NOT claimed. It is an opt-in local capability and requires owner device acceptance.
- The trusted-main `.github/workflows/windows-qa.yml` now triggers on Windows client changes after merge and checks WinGet *version only*, with no automatic install/update, no personal inventory upload and no untrusted PR execution. The GitHub connector used here did **not** expose a direct listing of main-only Actions runs/runner status: **actual self-hosted allocation and outcome remain UNVERIFIED**, never PASS by inference.
- This closes the safe owner-preview development tranche, NOT commercial marketplace production. Real publisher identity/approval, durable signing keys, signed public origin, code-signing certificate and physical owner-device install remain external prerequisites.
