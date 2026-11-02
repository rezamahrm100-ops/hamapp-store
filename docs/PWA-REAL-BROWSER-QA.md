# Actual Chromium browser acceptance — HamApp public PWA

Dedicated GitHub-hosted Linux workflow `.github/workflows/pwa-browser-acceptance.yml` builds the **validated** static site, installs pinned Apache-2.0 Playwright 1.64.1, launches a real headless Chromium and serves the generated site over localhost.

The test executes real DOM interaction for Persian store details, search/platform filtering, empty approved downloads, real service-worker activation, and **browser network-offline reload**. It asserts the offline catalogue is restricted to planned entries and never renders an approved download link. Screenshot evidence is short-lived, public-preview only. No application binaries or sensitive data are downloaded or published.

This test proves the current PWA safe navigation and cached planning content on a hosted Chromium browser. It is not a physical-device accessibility audit, full screen-reader test, web deployment provenance or production signed release acceptance.

Run locally only if Playwright is installed (use the workflow for reproducible hosted acceptance): `node tests/browser_pwa_smoke.mjs`, with `python scripts/build_site.py` and a local HTTP server serving `dist/site` on `127.0.0.1:8765`.
