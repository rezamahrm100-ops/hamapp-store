# HamApp Atlas UI — supported open-source design integration

## Accepted UI stack (native source retained)

- Android native Java: Google Material Components for Android **1.14.0**
  (`com.google.android.material:material`, Apache-2.0). New Material 3
  theme, MaterialButton, TextInputLayout/TextInputEditText and branded
  responsive rounded cards. Existing repository, publisher, package-install
  and user-consent logic remains **unchanged**.
  Upstream: https://github.com/material-components/material-components-android
  (maintained compatibility branch in maintenance mode; avoid converting the
  working application to Kotlin/Compose solely for appearance).
- Windows native Tkinter: **ttkbootstrap 2.2.6** on top of stock ttk
  (`bootstrap-dark` theme). WinGet and owned-catalog actions now use themed
  native ttk buttons and search/table styles. Hosted owner EXE build installs
  and bundles pinned dependency; source checks without optional library fall
  back to stock ttk/clam. WinGet shell-free engine, exact-ID confirmation
  and package readback remain identical.
  Upstream: https://github.com/israel-dryer/ttkbootstrap
  License expression: MIT AND (Apache-2.0 OR BSD-2-Clause), plus Pillow
  dependency with its own license. Keep notices when distributing binaries.
- Web/PWA: **self-contained original HamApp CSS** using visual conventions
  of the MIT-licensed Tabler/Bootstrap 5 RTL design system, but no upstream
  CSS/JS is vendored or loaded from third-party servers. This is deliberate:
  the existing Python-only offline and CSP-safe PWA must continue working
  under Iranian connectivity disruptions. Added a premium responsive visual
  layer with reusable color/radius/spacing tokens, RTL cards, search, status,
  focus outlines, dark/light and reduced-motion support. Tabler is a design
  reference, NOT a bundled library or upstream code fork.
  Upstream reference: https://github.com/tabler/tabler (MIT).

## Design tokens

| Role | Dark | Light |
| --- | --- | --- |
| Background | #0B1220 | #F4F7FB |
| Surface | #142136 / #17263A | #FFFFFF |
| Primary interaction | #9FE3C7 | #1B6655 |
| Secondary | #AEBFFF | #554EB0 |
| Text | #F3F6FC | #162337 |
| Outline | #30465E | #D5DFEB |
| Base radius | 14-24 px/dp | 14-24 px/dp |

Branding: Persian-first RTL, clear app source/publisher and status, no dark
patterns or auto-install. Fonts use available device/system families; no
unlicensed font files bundled. Every installation or update continues to
require native source verification and user/OS consent.

## Acceptance: no mock installs

- Android: build `:app:assembleDebug`, `:app:lintDebug`, emulator smoke,
  official signed F-Droid companion and real v1/v2 lifecycle.
- Windows: Python unit tests, full PyInstaller EXE and NSIS owner preview,
  actual isolated install/upgrade/uninstall, signer negative checks.
- Web: native PWA offline Chrome plus WCAG 2.1 AA serious/critical rules.
- Keep public release records, owner signing keys and approvals unchanged.
- Test outputs are owner-debug/unsigned previews, not commercial releases.
