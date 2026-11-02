# Milestones and acceptance gates

## V0 — first repository (implemented in this bundle)
- Public storefront + Persian RTL responsive UI.
- Client-side filters and search; initial app entries explicitly **planned**.
- Manifest, service worker, static build and tests.
- GitHub Actions CI, Pages workflow, Dependabot, opt-in Windows QA.
- One-file Windows bootstrap; first GitHub OAuth approval might be required.
- Gate: new GitHub repository exists, CI green, Pages deployed and accessible, site loads without JS errors.

## V1 — verified package distribution (NOT yet implemented)
- Inventory real current repos, license and release pipelines.
- Build metadata linking repo SHA, signed artifact, SHA256, platform and version.
- `fdroidserver` in offline/private signing environment; signed repo key fingerprint and independent backup.
- Security scanner integration, SBOM, signed release provenance, staged rollout/rollback.
- Genuine APK and Windows installer install/update QA on test devices.
- Gate: update continuity across 2 releases, corrupted artifact rejected, downgrade blocked, independent QA.

## V2 — branded native clients and management (NOT yet implemented)
- Reuse compatible F-Droid client source under GPL compliance and release a branded Android store.
- Native Windows software manager using verified installers / package sources.
- Publisher/admin dashboard, app screenshots, release notes, categories, multilingual support, download stats with consent, release review.
- Gate: verified security boundaries, installer prompt behavior, upgrade workflows and disaster recovery.

## V3 — multi-publisher marketplace (NOT yet implemented)
- Developer roles, signed publishing identities, moderation and malware review, private team distribution, optional payments.
- Gate: tenant isolation and external security review.

## Scope / cost

Bootstrap creates one public storefront repository to use GitHub Free public Pages and public Actions. Proprietary app source stays in existing private repos. Hosted GitHub Actions limits, traffic conditions and external storage prices must be monitored. A registered Windows runner for this new repository is separate from runners used by other private repositories.
