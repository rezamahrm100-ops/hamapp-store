# Open-source reuse — decisions before writing new code

Use mature upstream tools and native formats first. Record project URL, exact version/commit, license, maintenance status, threat model, update policy and test evidence before incorporation. A tool being open source does not grant permission to remove attribution or bypass its license.

## Android distribution
- fdroidserver (upstream https://gitlab.com/fdroid/fdroidserver): offline signed repository/index, package metadata and update primitives. Already used by offline stage adapter; production signing not yet accepted.
- F-Droid Android client (https://gitlab.com/fdroid/fdroidclient): potential branded client base. Investigate exact GPL obligations, trademarks, build reproducibility and Android installer restrictions first. No fork or binary claimed.
- Android SDK build-tools apksigner and aapt: signing-certificate/manifest inspection, not a substitute for policy/review; already integrated in publisher gate. Pin SDK version in future Android toolchain job.

## Windows distribution
- Windows Package Manager (winget / microsoft/winget-cli): use official packages/manifests where possible. For direct installer management, inspect App Installer/MSIX identity and Authenticode certificate continuity. Never force silent installation or bypass UAC.
- Existing Windows Authenticode verification: publisher gate uses PowerShell Get-AuthenticodeSignature; full Windows updater and version rollback safeguards remain unimplemented.
- Consider established frameworks for Windows GUI only if the target supports true app installation and security boundaries; an Electron-style wrapper around the PWA alone is not equivalent to a real installer manager.

## Web/admin
- Keep tiny static catalogue on Python standard library + PWA until actual accounts require a backend. For a future publisher dashboard, compare mature permissively licensed frameworks, OIDC providers, PostgreSQL and role permissions; select only after a documented security review.
- GitHub Releases for distribution, Actions for builds and attestations, CodeQL/Dependabot for security; do not implement Git hosting or CI from scratch.

## Evaluation gates for each dependency
Functionality match; pinned reproducible version; current maintenance and vulnerabilities; licensing compatibility (especially AGPL/GPL); security boundaries and update continuity; independent integration test; migration/exit strategy. Prefer a verified upstream adapter to a long-lived invasive fork.

Never claim F-Droid repository signature, Android/Windows installer readiness or source provenance solely from synthetic CI tests.
