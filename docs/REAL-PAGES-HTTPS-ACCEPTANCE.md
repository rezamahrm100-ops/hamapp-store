# Verified live GitHub Pages public HTTPS deployment — 2026-11-03

GitHub's successful `deploy-pages` action alone does not prove that the final public CDN delivered the same bytes produced by the build. `scripts/verify_live_pages.py` now performs real outbound HTTPS requests against the **fixed, first-party** `https://rezamahrm100-ops.github.io/hamapp-store/` origin after deployment.

The verifier checks actual `index.html`, `app.js`, `styles.css`, `sw.js`, `manifest.webmanifest`, `catalog/apps.json` and `catalog/planned-offline.json` against the exact local validated `dist/site` build. It rejects non-200 status, HTTP redirects, changed hostnames, mismatched response URLs, missing/symlinked source files, overlarge/unexpected content and any mismatch down to the byte. Uses Python SSL default CA chain and hostname verification rather than an insecure `curl -k`. The expected origin is hard-coded and must be owner-reviewed to change.

The Pages main workflow runs after actual deploy, allowing bounded retries for CDN propagation; a failure blocks the Pages workflow from being called accepted. A separate GitHub-hosted **read-only PR preflight** actually checks HTTPS against current main (only triggered by verification-workflow changes) so the verifier is tested against a real public site before any merge. Safe SHA-256/size-only receipts are retained in GitHub for five days.

## Direct local execution

```bash
python3 scripts/build_site.py
python3 scripts/verify_live_pages.py --site-dir dist/site --receipt /private/reports/hamapp-live-pages.json
```

This accepts live public homepage deployment content, **not** independently approved third-party web app origins in `catalog/trusted_web_origins.json` (still empty), nor immutable 40-character app release source commits, binary signatures, dynamic content/CDN future availability or a signed publisher release. No public application approval is activated. Live HTTPS parity is an observation at a particular run, not permanent tamper resistance.

## Acceptance

Review `HamApp Real Public HTTPS Pages Parity Preflight` workflow on its exact PR SHA and `Publish HamApp storefront` workflow on the exact merged main SHA. Both must show completed SUCCESS and short-lived parity receipt. Only then record accepted real first-party Pages parity. Older green builds do not substitute for the new post-deployment verification.
