# HamApp embedded engines — integrated 2026-11-08

## Scope and source-of-truth

This engineering tranche turns F-Droid native Android **package discovery,
signed-index validation and APK installation** into capabilities *inside* the
HamApp Android application. It does **not** import competing Droid-ify or
UniGetUI graphical shells, silently replace Windows Package Manager, or
pretend that Payload CMS and a WinGet REST server are necessary on a handset.

### Engines kept or integrated

- Android: `org.fdroid:index:0.2.0` Apache-2.0 library is the upstream
  repository JAR signature verifier; `InternalFdroidStore` streams a
  SHA256-verified index-v2 (up to 160 MiB) into a bounded native app list.
  `EmbeddedApkInstaller` checks downloaded APK bytes, exact package/version
  and APK signing certificate against that signed index. The Android OS
  PackageInstaller initiates install or upgrade after a dedicated
  per-app user confirmation; system security permission prompts are retained.
- Repository root: official F-Droid certificate fingerprint pinned from the
  upstream `default_repos.json` file and
  https://f-droid.org/docs/Release_Channels_and_Signing_Keys/ .
  The owner's separate HamApp repo remains disabled until a real approved
  signed F-Droid URL and independent fingerprint exist.
- Windows: retain the existing native HamApp WinGet explorer, interactive
  install/upgrade/uninstall, installed-state readback and NSIS installer.
  WinGet operations run as a child platform tool, not a separate store GUI.
- Web/PWA: retain offline and static hosted catalogue, which cannot perform
  arbitrary device package installation from browser JavaScript.
- Publisher backend: retain existing fdroidserver staging and native GitHub
  Releases integration. Commercial publisher identities, keys and approval
  records are external real-world prerequisites, not something to fabricate.

### Android explicit security boundaries

- `android.permission.INTERNET` fetches HTTPS metadata/APK only after the
  user starts an operation. The official signed index is about 70 MiB for the
  first load; a user confirmation explains network/storage cost.
- `android.permission.REQUEST_INSTALL_PACKAGES` is necessary for OS
  installation UI. A user must explicitly allow HamApp as an install source.
  Every session still requires Android's OS per-install confirmation.
- The index must be a single-signer JAR signed by the expected certificate.
  The index bytes and size must match its verified entry descriptor.
  Package versions are accepted only from this verified index.
- Before an install request, the APK's declared digest, size, package ID,
  versionCode and signing certificate must match the signed index. All
  redirects and unsigned sources are rejected, and Android enforces
  installed-certificate continuity and anti-downgrade independently.
- Planned or unapproved *HamApp-owned* catalogue apps remain disabled.
  Public official F-Droid packages are explicitly distinct from approved
  HamApp-owned publisher releases.

### Product and deployment limitations

- The user's first official catalogue refresh can consume 70+ MiB and internet
  connectivity. APKs have additional download cost. The verified cache is
  private and may be reused when current index digest matches.
- Repository correctness is based on actual library/CI build plus available
  device tests. A successful debug APK compilation does not assert real
  phone install/update, Android production approval, trusted stable app
  signing, or an active production store with proprietary releases.
- Android platform version and device policy may restrict unknown-source
  installation. The app must display that constraint; never bypass it.
- A signed public production store still requires genuine publisher
  binaries, registries, immutable versions, secure signing keys and backups,
  source provenance, and explicit owner release decisions.

## Upstream licenses

Apache-2.0 license text: third_party/fdroid-index/LICENSE.
Notices: android/app/src/main/assets/OPEN_SOURCE_NOTICES.txt.
