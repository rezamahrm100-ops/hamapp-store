# HamApp one-pass functional public-source discovery — 2026-11-08

This change extends the **existing** approved architecture, rather than importing overlapping package-manager shells.

- Windows: retain the integrated Microsoft WinGet discovery, exact-ID interactive install/upgrade/uninstall, and independent installed-state readback.
- Android: retain the official F-Droid companion as the only installer/updater. A new read-only in-app search uses the F-Droid documented public HTTPS search endpoint after user consent, displays bounded package results, and hands a chosen official F-Droid package URL to its installed client (with browser fallback). No APK downloads, sideloading, source switching or publisher approval from search output.
- Web/PWA: unchanged, keeps the same approved metadata and offline design.
- Approved proprietary catalogue: stays separate, with all planned entries disabled until *real* trusted publisher records and signed products exist.
- Toolchain: keep native Material 3, Windows WinGet/ttkbootstrap and upstream fdroidserver (private staging); no full Droid-ify GPL fork or UniGetUI duplicate shell is introduced.
- Network privacy: Android INTERNET permission is confined to a user-triggered HTTPS read-only query; the user is told that their search term goes to F-Droid. No background search, telemetry, installer privileges or storage access.

**Acceptance:** build Linux/Windows source CI and Android APK workflow on the exact PR SHA, then merge and collect Android and Windows artifacts from the merged main SHA. Physical-device acceptance, a production signing identity, durable F-Droid repository signing/key custody, publisher registration and actual owner-app listings remain independent real-world prerequisites. Never claim these from a debug preview or from official third-party search results.
