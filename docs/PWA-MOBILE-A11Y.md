# Hosted mobile-screen Chromium accessibility acceptance

Existing `.github/workflows/pwa-browser-acceptance.yml` now runs **actual mobile-sized Chromium** (390x844, Persian locale, RTL) and pinned upstream `@axe-core/playwright@4.14.0` after the existing real offline/service-worker test. It checks WCAG 2.0/2.1 A and AA rules for serious/critical violations in default dark theme, user-selectable light theme and native dialog; it also validates horizontal overflow, keyboard Enter dialog activation and Escape dismissal, and zero unapproved public download links.

Failure is real CI failure, not a paper waiver. The static site is served over local HTTP loopback and no private data or real installer is touched.

Automated axe results cover only a subset of accessibility: manual keyboard traversal, real assistive technology/screen readers, device/browser matrix, zoom 200%+, sensory/motor testing and localized usability still need separately evidenced review. Passing mobile WCAG smoke does not mean full WCAG compliance, production signing or a released marketplace.
