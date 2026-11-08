# HamApp — owner configuration without editing source

2026-11-08 | Scope: native Android and Windows clients, GitHub-hosted previews.

## Install and use

The native APK and Windows EXE/NSIS are packaged with their respective package
management engines. There is no step that checks out or modifies source code.
The Android F-Droid signed-index verifier uses upstream
`org.fdroid:index:0.2.0` plus Android's PackageInstaller. Windows continues to
run official system WinGet with explicit user consent from inside HamApp.

### Android: connect a personal signed repository

1. Open HamApp and choose **افزودن یا تغییر مخزن شخصی**.
2. Enter the canonical HTTPS `https://domain/fdroid/repo/` and its independently
   verified SHA-256 *repository signing certificate* fingerprint (64 hex).
3. Choose **ذخیره و بررسی امضا**, then browse the personal repository from
   HamApp. Repository entry and index digest verification must succeed before
   any package is displayed and considered for installation.
4. The Android OS still controls install-source permission and each install
   confirmation. The private profile can be removed in the same settings UI.

This is user-selected source trust, not owner-reviewed HamApp publisher
approval. The proprietary HamApp catalogue remains gated and cannot be changed
by personal preference settings. The private signing key must NEVER be entered.

### Windows: connect a private publisher intake account

1. Launch HamApp → **حساب‌ها و اتصال‌ها**. Public WinGet search/install/upgrade/
   uninstall needs no sign-in.
2. Enter the publisher identifier, the private intake service HTTPS root
   origin, a public CA certificate PEM file, an independently verified SHA-256
   fingerprint of the server's TLS leaf certificate, and the publisher's
   provisioned bearer token. Choose **ذخیرهٔ امن**.
3. The token is encrypted with **user-bound Windows DPAPI** and stored under
   `%LOCALAPPDATA%\HamAppStore\publisher-connection-v1.json`; source checkout
   and installers never contain real credentials. A blank token field during
   edit retains the encrypted secret. You can delete it from the UI.
4. Choose **بررسی TLS**. This performs certificate-chain + hostname + exact
   pin verification and a safe read-only 405 API probe. It does **not** claim
   bearer-token or publisher identity authentication.
5. If a *private publisher quarantine service* is actually deployed and
   provisioned, pick a genuine release `candidate.json` and APK/EXE/MSI/MSIX
   file, confirm a single upload, and choose **ارسال برای بررسی**. The client
   independently verifies exact release source/size/hash, performs pinned TLS
   before decrypting/sending the token, uploads only exact bytes, and accepts
   only a `quarantined` receipt. It does not approve or release the package.

The quarantine server depends on separately provisioned POSIX owner-private
directories, TLS cert/private key and publisher token registry. Only an operator
with the server and private credentials can provision that real service.
The client does not provision a server, invent a publisher, sign a program or
create a paid account. No browser-only authentication or public token exchange
is silently added.

### Trust and production

Owner-approved public releases still require durable Android signing and
F-Droid repository keystore custody (with independent backups), certificate
provenance, signed HTTPS repository, genuine approved binaries, and real device
acceptance. Windows Authenticode needs a real owner-controlled certificate.
Private keys belong in the signing environment, NOT in GitHub-hosted public
Actions, an APK or a desktop application. A debug-signed preview is not a
production release.

### Build and acceptance

Use existing `owner-installable-previews.yml` (no new infrastructure).
The targeted source tests cover settings, transport security and client UI
contracts. Hosted Windows tests exercise real DPAPI encrypt/decrypt without
disclosing user credentials; Linux CI covers strict source and checksum
rejection. The hosted Android workflow compiles the new settings dialog.
Owner Windows QA symlink-specific tests may SKIP if Windows denies creating a
test link (WinError 1314); Linux CI exercises the actual denial case. Do not
misreport those Windows-specific skips as a successful security test.
