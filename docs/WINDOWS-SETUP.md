# First-time Windows installation

Run the **one-file** `HamApp-SETUP.cmd` distributed with this project (the CMD embeds this source bundle; no companion download is required).

What it does:
1. Extracts only its embedded HamApp project sources to a temporary directory.
2. Uses WinGet to install Git/GitHub CLI if absent. A Windows installer/UAC prompt may appear.
3. Requests GitHub's normal browser OAuth authorization once if `gh` is not already authorized.
4. Creates `%USERPROFILE%\HamAppStore` *only if this folder does not already exist*.
5. Creates the **public** `owner/hamapp-store` repository, commits and pushes the storefront, tries to enable Pages, dispatches CI.
6. Attempts a separate, SHA256-verified repo-scoped Windows runner installation in `%LOCALAPPDATA%\HamAppStore`, starts it minimized, and writes `RUNNER-RESULTS.txt`. Failure does not affect other runners.
7. Writes `%USERPROFILE%\HamApp-SETUP-RESULTS.txt` even if something failed.

It does not alter existing GitHub repositories or runners, security software, network settings, service registrations, or private files (but it does add the new separate HamApp runner as authorized). It does not upload actual binaries. On rerun it recognizes its own existing clean project and an identifiably HamApp-owned repository; it never overwrites unknown repositories or uncommitted local work.

On setup success, a new HamApp runner is registered and its launch process is started. To reconnect later use the `START-HAMAPP-RUNNER.cmd` path in `RUNNER-RESULTS.txt`; `CONNECT-RUNNER.cmd` is for fresh registrations only. Windows QA jobs remain manual-only on trusted main.

Important: GitHub Actions workflows are executable code. Only start a self-hosted runner if you are comfortable letting this repository execute jobs under your Windows user account. Never grant jobs to untrusted PRs. Consider a dedicated low-permission Windows account or isolated VM for future builds.

## Troubleshooting: 404 on first run

The first setup incorrectly let Windows PowerShell 5.1 convert the expected
`gh repo view` GraphQL 404 into a terminating error. Setup v1.1 uses a
protected native-command wrapper and a REST existence check. If GitHub
returns 404, setup creates the new repository; other errors stop safely.

The setup is restartable: it reuses only a clean, marker-identified local
HamApp directory and a public GitHub repository with the expected project
description. Unknown state is never overwritten. The report records which
steps have actually run; publishing depends on successful GitHub Actions.
