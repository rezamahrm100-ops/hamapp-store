# هَماپ | HamApp

**همهٔ برنامه‌های ما، یک‌جا.**  Independent software storefront for Android, Windows, and web.

> Status (2026-11-05): **owner-installable native Android DEBUG APK, native unsigned Windows EXE/NSIS preview, and Persian RTL web/PWA**, with public-source browsing via official F-Droid and WinGet. Android/Windows proprietary catalogue entries remain **planned**, with no owner-approved binaries. Production signing, publisher releases, device-owner acceptance and paid marketplace operations are NOT established.

## نصب نسخه‌های آزمایشی فعلی (Android / Windows)

این نسخه‌ها برای **نصب و استفادهٔ آزمایشی شخصی** هستند؛ انتشار تجاری امضاشده نیستند. ZIPها در GitHub Actions موقت‌اند (۷ روز)، بنابراین برای دریافت ممکن است ورود به GitHub لازم باشد.

- **اندروید:** [دریافت فایل APK آزمایشی و راهنما](https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41914613853/artifacts/13363542959) — فایل `HamApp-Android-Preview-debug.apk` با امضای موقت Debug است. از داخل برنامه می‌توان با رضایت کاربر فروشگاه عمومی رسمی F-Droid را باز کرد.
- **ویندوز:** [دریافت برنامهٔ پرتابل و نصب‌کنندهٔ NSIS](https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41914613853/artifacts/13364660881) — فایل‌های `HamApp-Windows-Preview.exe` و `HamApp-Preview-Setup-UNSIGNED.exe` امضای تجاری ندارند. بخش WinGet جست‌وجو، اطلاعات، نصب/ارتقا، فهرست نصب‌شده‌ها و حذف انتخابی را با تأیید صریح کاربر فراهم می‌کند.
- در ویندوز، ZIP را استخراج و قبل از اجرای فایل‌های نصب، **`HamApp-Verify-Preview.cmd`** را اجرا کنید. این برنامه فقط SHA-256 و اندازهٔ فایل‌های بسته را کنترل می‌کند؛ معتبر بودن امضای ناشر را ثابت نمی‌کند و چیزی نصب نمی‌کند.
- **وب:** https://rezamahrm100-ops.github.io/hamapp-store/ — نمایش کاتالوگ مستقل، حالت روشن/تیره و دسترسی آفلاین.

جزئیات و موارد باز: [فهرست کمبودها و آزمون‌های پذیرش](docs/OWNER-READY-GAP-LEDGER-2026-11-05.md). اجرا و آزمون روی دستگاه واقعی مالک هنوز جداگانه لازم است.

## Features delivered

- Responsive RTL Persian PWA storefront with search, platform filters, dark/light mode, offline shell, and install prompt where supported.
- JSON catalogue schema + security validation. Planned apps cannot advertise unverified downloads.
- Automated tests, reproducible zero-third-party-dependency build, GitHub Actions CI, Pages deploy, Dependabot.
- Owner Windows QA on a separate repository-scoped self-hosted runner label (`hamapp-windows`), triggered by trusted main changes or manually.
- Native Java Android Material 3 UI (Google Material Components under Apache-2.0) with optional read-only official F-Droid HTTPS search results inside HamApp and an external official F-Droid client for all installs. Public search results are not HamApp publisher approvals. No GPL F-Droid client code or APK installer is embedded.
- Native Windows Python Tkinter/ttkbootstrap interface with separate official WinGet community browsing and independently checked interactive actions.
- Hosted owner-preview packaging for Android APK and Windows portable EXE/NSIS with SHA-256 receipt and one-click local integrity verification.
- A one-file self-extracting Windows `HamApp-SETUP.cmd` bootstrap distributed separately.

## Original first-time repository bootstrap (not required for preview installation)

1. Download and run **HamApp-SETUP.cmd** on your own Windows PC.
2. The launcher extracts the full project into `%USERPROFILE%\HamAppStore`, checks `git` and `gh`, and attempts installation through `winget` if missing.
3. If the GitHub CLI is not authorized, complete GitHub's **one-time** OAuth device/browser approval (no access tokens are collected by the script).
4. It creates **one new public repository** `YOUR_LOGIN/hamapp-store`. Store code and planned public app names are public. Your actual app source repositories stay separate and private.
5. It pushes `main`, enables GitHub Pages if the permission allows, and runs the CI.
6. The setup also **attempts to register and start a new repository-scoped Windows runner** in an isolated `%LOCALAPPDATA%\HamAppStore` subfolder after a verified official GitHub runner download. It never modifies existing project runners. If this step fails, inspect `RUNNER-RESULTS.txt` and retry via `CONNECT-RUNNER.cmd`.

A public storefront is deliberate to qualify for free GitHub Pages. Default catalogue entries are generic non-sensitive placeholders. Do not commit proprietary applications, secrets, signing keys or unreleased binary assets here.

## Local development

```bash
python3 -m unittest discover -s tests -v
python3 scripts/build_site.py
python3 -m http.server 8080 --directory dist/site
```

Open `http://localhost:8080`. The repository is static and needs no Node package manager or database to run. GitHub Pages URL is normally `https://YOUR_LOGIN.github.io/hamapp-store/` once enabled and deployed.

## Adding a release

A `released` catalogue item requires a semver-like `version` and HTTPS `download_url` to a validated official build. Do not simply mark apps released. APK signatures and provenance must be verified out-of-band until the signing pipeline is implemented. See [SECURITY.md](docs/SECURITY.md) and [ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Reusing upstream open source

- `fdroidserver` (AGPL-3.0): selected for **future signed Android binary repository/index**, integrated as an external tool; no upstream code copied into this repository.
- Existing F-Droid client (GPL-3.0 family): users may subscribe to our signed repository after it is prepared; a custom branded native client is a separate GPL-compliance workstream.
- GitHub CLI, Actions, Pages, releases, Dependabot: release automation and developer operations.
- The public storefront itself is tiny MIT-licensed glue, not a reimplementation of Android package management.

## Security boundaries

`HamApp-SETUP.cmd` performs an authenticated *new repository creation*, local Git initialization and a push. It never requests a PAT in the terminal, never uploads the contents of other folders, and never changes existing runners or Windows Firewall/VPN. `CONNECT-RUNNER.cmd` is an **additional opt-in action**. A public repo cannot use a private self-hosted runner for untrusted pull request workflows. See [security architecture](docs/SECURITY.md).

## Further documentation

- [System architecture](docs/ARCHITECTURE.md)
- [Roadmap and acceptance criteria](docs/ROADMAP.md)
- [Threat model](docs/SECURITY.md)
- [F-Droid upstream integration](docs/F-DROID-INTEGRATION.md)
- [Agent execution contract](docs/AGENT-IMPLEMENTATION.md)

## V1 publisher-verification foundation

The new [publisher pipeline](docs/PUBLISHER-PIPELINE.md) integrates `apksigner`, `aapt`, Windows Authenticode and upstream `fdroidserver` for owner-controlled **offline release candidate intake**. The trusted signer registry is deliberately empty. This tooling does not authorize public releases, prove build-source provenance, create signing keys or deploy APKs. Real signed artifacts and device acceptance are still required.

## Continuation for humans and AI agents

**Start with [AGENTS.md](AGENTS.md)**, then [engineering state](docs/ENGINEERING-STATE.md), [GitHub acceleration](docs/GITHUB-ACCELERATION.md), [open-source reuse](docs/OPEN-SOURCE-REUSE.md), and [next engineering batch](docs/NEXT-EXECUTION.md). Every new chat must independently inspect the current GitHub main commit and CI; these documents are working context, not substitutes for live checks.

GitHub build evidence is for the **static PWA bundle only**; it is not Android APK signing, Windows Authenticode, a production F-Droid repository or proof of real-device acceptance.

## Release continuity checks

See [release history and rollback protections](docs/RELEASE-HISTORY.md). This is an offline release review-only policy and does not publish packages or sign the F-Droid repository. Trusted signer and historical approval registers are intentionally empty until independently reviewed.

## Public-download admission policy

[Catalogue release approval gate](docs/CATALOG-RELEASE-GATE.md) refuses unapproved Android/Windows download buttons even when a HTTPS link is present. It cross-checks independently reviewed publisher and history metadata, but cannot replace actual signature/provenance/device verification. Web-app release policy remains a separate workstream.

## Native Windows client preview

The [Windows desktop client](docs/WINDOWS-CLIENT.md) uses Tkinter + Microsoft's winget and is built as a short-lived unsigned preview EXE on GitHub-hosted Windows. Its source lives under `windows_client/`; the preapproved package map `catalog/winget_packages.json` starts empty, and download/install buttons cannot be enabled without independent publisher, version, and package mapping review. This is not an installed or signed production app.

## Native Android client preview (GitHub-hosted build)

A minimal **native Android Java** RTL catalogue app now lives under [android/](android/) and uses the existing F-Droid client as an optional package-installer companion. It does not fork or redistribute F-Droid's GPL source. See [Android client notes](docs/ANDROID-CLIENT.md). GitHub-hosted Android CI builds a **debug-signed preview APK** (not production). Trust registration is intentionally absent: `catalog/android_repository.json` contains null, and every install action stays disabled. Read the actual Android workflow outcome and signing key before claiming installable production readiness.

## Android native app and emulator-verified preview

The [native Android app](docs/ANDROID-CLIENT.md) now builds a **debug APK** on hosted GitHub Actions with Gradle and Android SDK. A separate [hosted emulator smoke test](https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41488084733) installed and launched the native Java RTL app and checked that unapproved F-Droid actions stay disabled. **Debug signing is not production signing**; no approved publisher or signed F-Droid repo exists yet. No install controls are active and no production Android app release has been published.

## Native preview artifact provenance

GitHub-hosted Android debug APK and unsigned Windows EXE now produce main-only cryptographically signed GitHub build attestations, independently checked with gh attestation verify against a fixed producing workflow and source SHA. See [build provenance](docs/NATIVE-PROVENANCE.md). These are **not** developer signing identities or production app releases.

## F-Droid signed index verification preflight

A separate [F-Droid signed-index verifier](docs/FDROID-INDEX-PREFLIGHT.md) now reuses fdroidserver's index-v2 verifier, demanding a separately pinned repository URL and signing key fingerprint. It rejects missing or unapproved repositories, never generates keys and does not approve package downloads. Production F-Droid key and signed index do not exist yet.

## Actual F-Droid signature pipeline rehearsal

A [hosted isolated signed-index drill](docs/FDROID-ISOLATED-SIGNED-INDEX-DRILL.md) builds a real signed index-v2 with upstream fdroidserver using a **disposable** signing identity; validates the correct fingerprint and rejects an altered index or wrong fingerprint. It has no release rights and never publishes signing secrets or an installable production catalogue. Acceptance requires a green run of the dedicated GitHub workflow.

## Real emulator two-version upgrade smoke

The [two-version Android acceptance test](docs/ANDROID-TWO-VERSION-SMOKE.md) uses the actual Android 35 Package Manager to install and upgrade HamApp between two temporary debug-signed versions, checks downgrade refusal and the native UI after upgrading. It cannot substitute for a stable signed production/F-Droid app update.
