# HamApp — architecture

## Engineering goal

Ship an independent cross-platform release centre without rebuilding package distribution primitives. **Current V0:** public zero-backend PWA storefront with app metadata and real CI/CD. **Future V1:** signed F-Droid repository and explicit download provenance. **Future V2:** branded native Android client using F-Droid code under its licence, Windows update agent, and administrative publishing UI.

## Flow

Existing private app repositories -> CI release artifacts and signature verification -> trusted publishing adapter -> validated catalogue and signed Android repository -> GitHub Pages/CDN -> end-user store (PWA, then native client).

- **Catalogue:** versioned `catalog/apps.json`, an intentionally simple public data contract.
- **Frontend:** static RTL PWA, accessible controls, controlled DOM writes, HTTPS-only outbound links, no analytics or personal user data.
- **CI:** Python built-in `unittest`; independent GitHub-hosted Linux validation; Pages publish only from `main`.
- **Owner QA:** manual workflow on `hamapp-windows` label, with job permissions restricted and no global system modifications.
- **Android repo:** use upstream `fdroidserver`, with persistent offline signing key and reproducible generated indexes; never generate production signing identities on an ephemeral runner or commit key material.
- **Windows:** use signed installer/MSIX or installers with verified hash provenance. Future auto-updates need per-app signature checks and anti-rollback.
- **Private listings:** cannot be safely hidden by filtering a static public JSON file. Requires authenticated server-side API, explicit access policy, and separate private artifact hosting.

## Hosting tradeoffs

GitHub Pages for public static content is normally free and needs no domain. GitHub Releases is useful for versioned assets, but is not an unrestricted CDN. If download volumes or private distribution grow, migrate signed binaries to object storage/CDN while retaining the same catalogue contract. Keep existing app source repositories private; a public storefront does not imply publishing proprietary code.

## Data contract

Every app must have `id`, `name_fa`, `name_en`, `description`, `platforms`, `status`, `version`, `download_url`. Planned entries have `null` version/link. Released entries have validated semantic version, HTTPS link; adding signing/provenance fields is a future breaking/extended schema change.

## Update strategy

A website PWA updates its own content but cannot directly silently install or update Android APKs or Windows EXEs. Android update installation remains subject to platform consent, package identity and certificate continuity. Use F-Droid's open client/store protocol for normal update discovery; enterprise/device-owner paths have different constraints.
