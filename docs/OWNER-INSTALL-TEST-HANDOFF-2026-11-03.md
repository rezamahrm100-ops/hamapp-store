# HamApp — owner install/test handoff, 2026-11-03

This handoff supersedes the earlier requirement to delay *preview delivery* until every official F-Droid real-client upgrade integration is green. It **does not** claim production/storefront acceptance or waive code/signature safety.

## Exact main source/build
- Main SHA: `4213d05f76a46417db135e487a4c7246d2dd3aba`.
- Merged code PR [#80](https://github.com/rezamahrm100-ops/hamapp-store/pull/80).
- Native owner-installable Actions build: [#41696010045](https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41696010045), two jobs SUCCESS.
- Same-head CI #41696010370 SUCCESS, CodeQL #41696010035 SUCCESS, source security #41696010205 SUCCESS, Pages #41696010036 SUCCESS, evidence #41696010141 SUCCESS.
- Self-hosted owner Windows QA #41696010226 QUEUED. Never mark as passed without actual log.

## Installable artifact inventory

| Platform | File | SHA256 | Reality/trust |
| --- | --- | --- | --- |
| Android | `HamApp-Android-Preview-debug.apk` | `75d37f7da4377f3c12e8291d050de16a7a4705ca9d8892f28c53fb4c799bfed8` | Real APK 15,214 bytes; **debug-signed**, not production |
| Windows portable | `HamApp-Windows-Preview.exe` | `0e86962cdaded1fc8a08b8676bb5c0f3e4d78da62d85381c22eccfc7867b8a97` | Real PyInstaller PE 11,406,183 bytes; **unsigned** |
| Windows Setup | `HamApp-Preview-Setup-UNSIGNED.exe` | `2be171bcd40537cedf19c42097fe4fc5d30114ad82666df3c9e0940117e086b2` | Real NSIS per-user package 11,175,851 bytes; **unsigned** |

Download from GitHub Actions run #41696010045 under *Artifacts*: `HamApp-Android-Owner-Test-APK`, `HamApp-Windows-Owner-Test-EXE-Setup`. Each includes `README_FA.md`, `manifest.json` and `SHA256SUMS.txt`. Retention 7 days; this is **not** a public release and permanent distribution URLs are intentionally absent.

### Owner testing, no remote or surprise install

1. Verify exact file SHA256. On Windows: `Get-FileHash .\HamApp-Windows-Preview.exe -Algorithm SHA256` or same for Setup; Android APK can be verified with a local file hashing tool.
2. Install Android debug APK only on a device you choose, with your own Android permission consent. A prior app with a distinct debug signer may refuse in-place update; exporting data first matters.
3. Windows use `HamApp-Preview-Setup-UNSIGNED.exe` if testing installer/uninstall, or `HamApp-Windows-Preview.exe` for no-install portable run. Do not bypass OS security prompts unless you independently trust the source and SHA256.
4. Note OS version, which preview file, launch result, UI/display/search problems, exact expected vs actual and screenshots with sensitive personal data removed. Send results back in chat. No credentials, keys, proprietary source or private logs needed.
5. The apps are planned-only demonstration catalogue/UI pending approved publisher packages; do not expect working third-party commercial downloads or public signing from these files.

## Real engineering still missing
These previews do **not** close multi-publisher identity/account/MFA/moderation, approved third-party package metadata/downloads, real production F-Droid origin/certificate/offline key backup, first-party release/attestation authorizations, positive production Windows Authenticode/WinGet, or complete native product UX/feature goals. Official upstream F-Droid app-in-client v1 install succeeded on a disposable emulator previously, but v2 full in-client upgrade remains unverified in open PR #72; the separate standalone HamApp debug APK is fully independent of that test. No physical-owner device approval or certified release exists. Main ruleset still absent (Issue #31); requires repo admin. Public catalogue downloads disabled.

**Engineering verdict:** owner-installable *preview delivery* PASS, whole-product technical closure **PARTIAL**, production release **NOT APPROVED**.
