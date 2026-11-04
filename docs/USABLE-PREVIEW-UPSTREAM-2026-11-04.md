# HamApp usable preview — public upstream sources (2026-11-04)

## Problem solved by this tranche

The checked-in HamApp-owned catalogue contains only three **planned** entries
and no approved APK, Windows package, stable publisher identity or public
download. A branded app that only shows those cards is installable but cannot
install any software. Rather than fabricate approval or fork vast upstream
GUIs, this implementation adds a **separate opt-in external-source mode**
beside the owner-reviewed HamApp store.

### Android

- The native HamApp screen now offers **Open public F-Droid catalogue**.
- This invokes the installed official `org.fdroid.fdroid` launcher after an
  explicit dialog. Android 11+ manifest package visibility is restricted to
  that one package; no QUERY_ALL_PACKAGES, INTERNET or
  REQUEST_INSTALL_PACKAGES permission is added.
- If F-Droid is absent, the user can open the fixed
  `https://f-droid.org/` official website using Android ACTION_VIEW.
- Android handles any external browser/installation prompts; HamApp does not
  sideload, download, grant permission or invoke package installation.
- The independent HamApp-signed repository handoff remains gated by actual
  owner-approved URL, certificate fingerprint and release history, unchanged.
- App cards now expose a native details dialog rather than only disabled
  install controls.

### Windows

- The native preview has an **Explore WinGet** window, separate from
  HamApp-owned planned apps.
- Read-only search uses official `winget search --query ... --source winget`
  and `winget show --id ... --exact --source winget`.
- Display results only when a strict ID can be parsed from the actual official
  CLI table. Ambiguous/localized output is visible as plain text but yields no
  actionable package ID. No remote manifest is treated as HamApp approval.
- A selected package can be installed or upgraded **only after its exact source
  metadata is checked and the user explicitly confirms the external-source
  warning**; native WinGet retains its installer, UAC and EULA prompts.
- Install CLI uses exact ID, `--source winget --interactive --no-upgrade`.
  Upgrade requires an installed identity and uses `--interactive`.
- No silent installs, acceptance flags, force, shell interpolation, custom URL,
  unknown alternative repository, or privilege escalation are introduced.
- After a successful CLI command, HamApp reads the registered package version
  independently through the existing official WinGet export adapter.
- Unlike owner-published apps, an independently selected WinGet community
  package is **NOT verified or approved by HamApp as a publisher**. Microsoft
  WinGet provides its own manifest/checksum and installer flow. The user
  remains responsible for source and license evaluation.

### Web/PWA

- Public external F-Droid and Microsoft WinGet documentation links are shown
  in a clearly separate section. They are not presented as HamApp-owned
  downloadable releases.
- Original release links remain restricted to reviewed signed metadata.
- Offline PWA shell cache is incremented for the visible new layout.

## Open-source reuse decisions

| Component | Used as | License / notes |
| --- | --- | --- |
| Official F-Droid Client | External Android app / launcher | GPL-3.0-or-later; no binary or source copied into HamApp |
| fdroidserver | Existing private signed-index stage adapter | Existing license and key custody procedures unchanged |
| Microsoft WinGet CLI | Native Windows package discovery/install backend | Existing platform utility; source pinned to `winget`; no upstream code bundled |
| UniGetUI | Optional upstream implementation reference only | Not bundled; adding a second WinGet GUI would duplicate capabilities and enlarge maintenance |

No local key is created, no producer attestation is asserted for third-party
packages, and no external installer binary is vendored into the public repository.

## Installable owner preview acceptance contract

- Pull request tests: standard 12+ GitHub workflows, hosted Windows/Android
  binaries, real emulator F-Droid and package lifecycle, CodeQL, ClamAV,
  PWA browser. Include separate negative unit tests for external search,
  approval separation, argument injection and no source-consent bypass.
- Owner test download: `.github/workflows/owner-installable-previews.yml`
  artifacts `HamApp-Android-Owner-Test-APK` and
  `HamApp-Windows-Owner-Test-EXE-Setup`, each with SHA256 and Persian notes.
  These are DEBUG Android and UNSIGNED Windows builds, not signed production
  builds; artifacts are short-lived.
- On Windows, install the EXE setup or launch portable EXE, choose
  `کاوش و نصب نرم‌افزارهای عمومی از WinGet`, search for an installed/desired
  package, inspect exact metadata then approve if desired.
- On Android, install the debug APK and choose
  `بازکردن فروشگاه عمومی F-Droid`; the separately installed official
  app opens, or the official website is shown if absent.
- No third-party package is installed automatically during app setup or
  without a separate user action. No owner device is remotely operated.

## Still not a production marketplace

Missing owner/external gates: verified HamApp publisher binaries, developer
code-signing identities, durable private F-Droid signing key/offline backup,
production HTTPS origin, commercial marketplace roles, independent customer
device tests and signed Windows release certificates. External-store use
cannot be conflated with a HamApp-owned production release. The goal of this
tranche is a **functional installable personal-use preview** rather than a
fully accredited app marketplace.
