# HamApp signed source refresh — opt-in background lifecycle (2026-11-08)

## Architecture: existing signed F-Droid trust, official Android scheduler

The native Android application now uses official `androidx.work:work-runtime:2.12.0`
for optional WorkManager-backed repository catalogue refresh. The WorkManager
version is pinned to a Google stable release, not pulled dynamically.
This worker is not a second installer, new downloader, private publisher API or
custom app store. It invokes **the exact existing** `InternalFdroidStore`
signed `entry.jar`, SHA256/size, signed-index-timestamp rollback and atomic
private cache path, shared with the foreground UI.

The owner decides from a native RTL settings button:
- Off by default; merely installing HamApp or adding a repo never opts in.
- Opt-in daily unique worker, Wi-Fi/unmetered plus battery-not-low only.
- Optional explicit manual refresh, with the same network constraints.
- Disabling cancels both scheduled and manual work.
- Saved outcome counts only successfully verified personal repositories and
  shows the latest completed timestamp and a generic failure state; no token,
  source URL or private key is written to worker logs.
- Each of the maximum six independently signed personal subscriptions is checked
  against its current URL + out-of-band fingerprint on every run. Deletion of
  source trust and removal of cached receipts are synchronized with ongoing
  refresh so background work cannot silently restore revoked trust.
- A failed signature, index rollback/equivocation, network error or missing
  source configuration never permits a new downloadable package or auto-install.
- Only signed **catalogue metadata** is refreshed. APK downloads, OS install
  requests, silent app upgrades, publisher admissions and deployment remain
  deliberately absent from periodic/background work.
- Never claims that a background run executed at an exact wall-clock time:
  WorkManager scheduling is delayed by system power/network policy.

## Acceptance

PR acceptance requires all hosted Linux/Windows CI, CodeQL, source security scan,
Android `assembleDebug` and `lintDebug`, real APK permission allowlist, hosted
Android 35 UI smoke and actual instrumented WorkManager opt-in/cancel test.
Real native APK source metadata and debug signing must remain test-only.
The workflow's `connectedDebugAndroidTest` verifies Android private preferences
and queries the actual WorkManager unique periodic work; a unit source scan is
NOT a substitute for that device test. Results are **PENDING** until exact
GitHub workflow ids and terminal conclusions are inspected.

## Remaining full client gaps

This is not full F-Droid parity: no multi-source SQL delta/index-v2 entry
management, verified mirror fallback, resumable APK download queue, background
notifications of *installed-app* updates or auto upgrade are claimed.
Actual source signatures for real publishers, immutable production repository
key custody, HTTPS publication, physical owner device install/update acceptance
and payment functionality remain genuine owner/engineering gates.
