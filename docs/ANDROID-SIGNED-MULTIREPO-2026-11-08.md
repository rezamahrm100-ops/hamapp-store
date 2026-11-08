# HamApp — signed multi-repository and offline read-only catalogue (2026-11-08)

## ACCEPTED IMPLEMENTATION — PR #95

PR https://github.com/rezamahrm100-ops/hamapp-store/pull/95 merged at source SHA
`4250f4b78cc8bf882aef197f8731c322154564c5`, with all ten review-head workflows SUCCESS.
Hosted native Android 35 emulator completed four instrumented state/trust
tests and strictly disabled unapproved app installs; exact run
https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/42497086808. Android preview package, private service,
CodeQL, ClamAV and source checks passed on PR. Post-merge main run links
and actual artifact IDs are in docs/ENGINEERING-STATE.md. The old
"PENDING" acceptance language below was written before these checks.

Do not claim full F-Droid client parity or product release: offline
catalogue is read-only; background update/mirrors/delta databases and
publisher production signing, owner account activation and real-device
acceptance remain separate gaps.


## Scope and upstream reuse

The Android application continues to use the upstream Apache-2.0 F-Droid
`org.fdroid:index:0.2.0` JAR entry verifier plus the Android operating system
`PackageInstaller`. It does not vendor or impersonate the GPL full F-Droid
client, or invent a separate package installer. The official F-Droid repository,
each user-added repository, and the still-empty owner-approved publisher
registry remain separate trust domains.

## Functional implementation

- Up to six user-configurable HTTPS repositories, each with its own independently
  provided SHA-256 signing-certificate fingerprint. Android stores these
  in per-app private preferences. A duplicate URL or a silent fingerprint change
  is rejected; explicit removal and re-addition are required for rekeying.
- Existing single-repository settings are read as a legacy record and migrated
  without rewriting its fingerprint when the first new repository is added.
  Malformed or ambiguous stored sources fail closed.
- Each source retains its own index digest and exact byte count from an actually
  signature-verified F-Droid `entry.jar`. The streaming index is stored in an
  app-private per-origin, per-fingerprint namespace. New bytes replace existing
  ones using atomic file-system move, with no delete-first fallback.
- Offline browsing re-hashes the file and checks its saved origin-bound digest
  and size. It NEVER authorizes an APK install: no offline browse details screen
  has an install button. A fresh authenticated online repository entry and APK
  digest and publisher-certificate checks still precede system installation.
- Deleting a source removes its saved index receipt and cached file but does not
  uninstall any application on the device. Existing official public F-Droid
  browsing remains separate and available.

## Actual acceptance

The native Android emulator workflow now runs
`gradle --no-daemon -p android :app:connectedDebugAndroidTest` *on the already
booted hosted Android 35 emulator*, following the existing strict RTL UI smoke.
Instrumentation verifies actual Android private-preference persistence,
multiple source pins, migration from legacy settings, rejection of signer
substitution/duplicate sources, broken trust state, and absence of a usable
offline cache before a verified receipt exists. Real test-result XML is saved
in the emulator evidence artifact. Hosted Gradle `assembleDebug`, `lintDebug`,
Python tests and CodeQL remain mandatory. These checks are PENDING until
their exact GitHub run verdict has been inspected.

## Security and scope limits

This is **not** a complete F-Droid 2.x client replacement. Full repository
database and signed index delta management, verified mirror selection,
resumable transfer and controlled background update notifications remain
unfinished. An older locally verified index is intentionally read-only while
offline; independently verifying the newest publisher release requires a fresh
trusted index and online artifact. Public catalogue promotion, production
developer signing, independently verified publisher identity and physical
device user-consent acceptance are unchanged external gates.

Never treat a debug APK, test fixture, recorded fingerprint, private repository
setting or CI success as a production-approved app release.
