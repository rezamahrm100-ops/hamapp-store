# HamApp UI-backend integration contract (2026-11-04)

## Decision: reuse working upstream engines, not vendor their entire graphical shells

The store already uses: official F-Droid via explicit `fdroidrepos://` ACTION_VIEW,
`fdroidserver` for separately controlled signed repository staging, Microsoft's
WinGet for interactive install/upgrade and installed-version readback, and a
validated static web/PWA catalogue. Keep these upstream engines instead of
copying hundreds of unrelated UI files into HamApp.

UniGetUI (https://github.com/Devolutions/UniGetUI, MIT) is an excellent reference
implementation and optional standalone package-management application, **not**
a dependency needed to access WinGet. Forking its complete UI would conflict
with the intended dedicated HamApp UI, expand the supply-chain surface and
require tracking every upstream release. Do not download or execute its latest
installer in PR CI. If a future request needs other package-manager integrations,
review UniGetUI's published CLI/IPC contract and permissions separately.

F-Droid Client (https://gitlab.com/fdroid/fdroidclient, GPL-3.0-or-later) remains
an official separately installed companion; it has **not** been imported,
rebranded, licensed as MIT or embedded. A real fork requires GPL-compliant
source redistribution, trademark review, an ongoing upstream rebase strategy,
and Android package-install permission analysis.

## Output: read-only UI backend contract

`scripts/build_ui_contract.py` emits `hamapp-ui-backend-v1`, a deterministic
JSON snapshot of approved actions, using **the same trusted catalogue**
as native Android, Windows and web builds:

- Android: `official-fdroid-companion`, `open_signed_repository`;
  enabled only for an approved Android release **and** owner-approved
  signed repository URL+fingerprint. This opens F-Droid, not the OS installer.
- Windows: `microsoft-winget`, `request_interactive_operation`;
  enabled only for an approved release with owner-reviewed WinGet identity,
  version and exact artifact digest. Runtime operations must use
  `windows_client.core.command_for / execute_operation`, which retain
  explicit confirmation, native version readback and downgrade denial.
- Web: `verified-https-origin`, `open_approved_web_release`;
  enabled only after existing signed-off web origin and release history
  validation. This is a browser launch, not native installation.

The contract has `schema_version`, `contract`, `catalog_sha256`, `engines`
and per-app `platforms` capability objects. It is generated into:

| Consumer | Generated location |
| --- | --- |
| PWA | `dist/site/catalog/store-capabilities.json` |
| Android native build asset | `android/app/src/main/assets/store-capabilities.json` |
| Windows native preview and packaged EXE | `dist/windows-client/store-capabilities.json` |
| Independent pipeline/UI tests | `dist/ui-contract/store-capabilities.json` |

Generation: `python scripts/build_ui_contract.py`, or the normal
`build_site.py`, `build_android_catalog.py`, and
`build_windows_client_catalog.py` commands. Existing release validation
runs **before** any action can become enabled. CI and preview workflows now
check generation and package the native read model; independent tests
assert deterministic output, rejects unapproved packages, invalid repos and
ghost download links. Files are generated, not checked-in release approvals.

### Important boundary

The JSON contract is a **view model, never a security authority**.
Native clients must revalidate and authorize an action against their own
approved embedded manifest at invocation time. Do not permit JavaScript or
untrusted local edits to invoke WinGet, F-Droid install, or any privileged
system operation. Read-only action flags do not mean the package is installed,
the user granted installation permission, the binary is scanned/signed by an
approved publisher, or the operating system accepted an update. UI should
display `enabled=false` and its explanatory state for planned entries.

## UI design next: no new package engines required

Build dedicated Persian RTL interfaces on top of the native clients' existing
execution adapters plus the shared capability snapshot. Keep install consent
and signed-release approval in the existing native/release gates. UI designers
may freely replace card/detail/navigation presentation without redefining
publisher identity, manager commands, or package metadata.

**Still external/production gates:** publisher identity and real release
approval, production Android and Windows certificates, persistent owner-held
F-Droid signing key/offline backup, independently trusted public HTTPS origin,
and accepted live install/update on owner devices. PR #72 independently tracks
a real official-F-Droid v1-to-v2 client update; do not call it passed until
the exact source workflow confirms it. Public downloads remain disabled.
