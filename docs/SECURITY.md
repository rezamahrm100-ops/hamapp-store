# HamApp security model

- **Never commit:** PFX/JKS/keystore, signing passwords, access tokens, API keys, private APK binaries, user data or the `.gh` credentials store.
- **No arbitrary publisher upload:** a static public catalogue is not an authorization service. A future ingest endpoint must authenticate release publishers and verify binary signature, checksum, provenance and ownership.
- **Public PRs must not execute self-hosted jobs:** the owner Windows QA workflow is manual-only on `main`. No `pull_request_target`, `workflow_run`, user-controlled run commands or arbitrary artifact execution.
- **No secrets in CI:** public GitHub-hosted jobs build only static site files using read-only checkout and short-lived GITHUB_TOKEN permissions.
- **Integrity:** F-Droid signed repository index must be produced with a persistent trusted key kept separately from the public repo and web server; certificate fingerprints must be distributed via a trusted channel. APK updates require same package ID and developer signing certificate.
- **Windows runner:** installation in a separate directory, **not** a system service, after this requested one-click bootstrap. It is confined to the Windows user account, not an OS service. Self-hosted workflows run arbitrary code from repo; keep owner branch protected and do not use the runner for unreviewed pull requests. Runner is started manually in its own terminal.
- **Dependency safety:** upstream tooling versions and licenses should be pinned and reviewed before production; auto-merging Dependabot PRs is disabled.
- **Production release:** signed binaries, hashes, attestations, provenance, malware scanning, failure rollback, backups, and full installation tests are required before marking an item released.
- **Initial state:** no user accounts, telemetry, downloads or updater. Initial catalogue is demonstrative, not a claim that specific apps are installable.

## Candidate intake trust boundary

The new publisher gate accepts only exact owner-approved signing certificate fingerprints and fails closed when unregistered. Signing keys and offline F-Droid configuration never belong in this repository or on CI runners. A verified candidate receipt is not permission to publish, and declared source commit SHA is **not verified provenance**. See `docs/PUBLISHER-PIPELINE.md`.
