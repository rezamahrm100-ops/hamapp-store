# هَماپ | HamApp

**همهٔ برنامه‌های ما، یک‌جا.**  Independent software storefront for Android, Windows, and web.

> Status: usable static PWA catalogue + GitHub CI/Pages automation. A native Android store client, binary repository signing, APK installation and update agent, paid accounts, and publisher portal are NOT implemented. The initial entries are clearly marked **planned** and have no download links.

## Features delivered

- Responsive RTL Persian PWA storefront with search, platform filters, dark/light mode, offline shell, and install prompt where supported.
- JSON catalogue schema + security validation. Planned apps cannot advertise unverified downloads.
- Automated tests, reproducible zero-third-party-dependency build, GitHub Actions CI, Pages deploy, Dependabot.
- Optional owner Windows QA on a separate repository-scoped self-hosted runner label (`hamapp-windows`), dispatched manually only.
- A one-file self-extracting Windows `HamApp-SETUP.cmd` bootstrap distributed separately.

## First run

1. Download and run **HamApp-SETUP.cmd** on your own Windows PC.
2. The launcher extracts the full project into `%USERPROFILE%\HamAppStore`, checks `git` and `gh`, and attempts installation through `winget` if missing.
3. If the GitHub CLI is not authorized, complete GitHub's **one-time** OAuth device/browser approval (no access tokens are collected by the script).
4. It creates **one new public repository** `YOUR_LOGIN/hamapp-store`. Store code and planned public app names are public. Your actual app source repositories stay separate and private.
5. It pushes `main`, enables GitHub Pages if the permission allows, and runs the CI.
6. The setup also **attempts to register and start a new repository-scoped Windows runner** in an isolated `%LOCALAPPDATA%\HamAppStore` subfolder after a verified official GitHub runner download. It never modifies existing project runners. If this step fails, inspect `RUNNER-RESULTS.txt` and retry via `CONNECT-RUNNER.cmd`.

A public storefront is deliberate to qualify for free GitHub Pages. Default catalogue entries are generic non-sensitive placeholders. Do not commit proprietary applications, secrets, signing keys or unreleased binary assets here.

## Local development

```bash
python3 -m unittest discover -s tests -v
python3 scripts/build_site.py
python3 -m http.server 8080 --directory dist/site
```

Open `http://localhost:8080`. The repository is static and needs no Node package manager or database to run. GitHub Pages URL is normally `https://YOUR_LOGIN.github.io/hamapp-store/` once enabled and deployed.

## Adding a release

A `released` catalogue item requires a semver-like `version` and HTTPS `download_url` to a validated official build. Do not simply mark apps released. APK signatures and provenance must be verified out-of-band until the signing pipeline is implemented. See [SECURITY.md](docs/SECURITY.md) and [ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Reusing upstream open source

- `fdroidserver` (AGPL-3.0): selected for **future signed Android binary repository/index**, integrated as an external tool; no upstream code copied into this repository.
- Existing F-Droid client (GPL-3.0 family): users may subscribe to our signed repository after it is prepared; a custom branded native client is a separate GPL-compliance workstream.
- GitHub CLI, Actions, Pages, releases, Dependabot: release automation and developer operations.
- The public storefront itself is tiny MIT-licensed glue, not a reimplementation of Android package management.

## Security boundaries

`HamApp-SETUP.cmd` performs an authenticated *new repository creation*, local Git initialization and a push. It never requests a PAT in the terminal, never uploads the contents of other folders, and never changes existing runners or Windows Firewall/VPN. `CONNECT-RUNNER.cmd` is an **additional opt-in action**. A public repo cannot use a private self-hosted runner for untrusted pull request workflows. See [security architecture](docs/SECURITY.md).

## Further documentation

- [System architecture](docs/ARCHITECTURE.md)
- [Roadmap and acceptance criteria](docs/ROADMAP.md)
- [Threat model](docs/SECURITY.md)
- [F-Droid upstream integration](docs/F-DROID-INTEGRATION.md)
- [Agent execution contract](docs/AGENT-IMPLEMENTATION.md)

## V1 publisher-verification foundation

The new [publisher pipeline](docs/PUBLISHER-PIPELINE.md) integrates `apksigner`, `aapt`, Windows Authenticode and upstream `fdroidserver` for owner-controlled **offline release candidate intake**. The trusted signer registry is deliberately empty. This tooling does not authorize public releases, prove build-source provenance, create signing keys or deploy APKs. Real signed artifacts and device acceptance are still required.
