# Actual official F-Droid Android-client repository persistence acceptance

## The gap this tests

Prior accepted [PR #62](https://github.com/rezamahrm100-ops/hamapp-store/pull/62) **genuinely proved** that an unmodified, independently GPG+Android-signer-verified official F-Droid APK on a hosted Android 33 emulator issued real HTTPS requests for two separately signed versions of a real disposable F-Droid index. That alone **did not prove the repository persisted in the client's own database**. An HTTP request could come from a transient add-repository preview or metadata fetch.

This feature attempts an additional independent **read-only native SQLite proof**, without bypassing official UI or writing a forged database row.

## Mechanism and security

After the previously accepted v1→v2 real HTTPS network test in the *same* disposable Android emulator, `scripts/fdroid_official_repo_db_probe.py` uses the already-rooted, short-lived **hosted emulator only** to take an in-memory bounded `adb exec-out tar` snapshot of `/data/user/0/org.fdroid.fdroid/databases`. It never reads an actual device. The tar extractor rejects symlinks, hardlinks, traversal, unexpected filenames or excessive sizes, then writes any SQLite files into a 0700 temporary directory within `RUNNER_TEMP`, destroyed before artifact upload. It verifies real SQLite `PRAGMA quick_check` in read-only mode, enumerates repository tables, and requires **exactly one** actual database containing the expected ephemeral `10.0.2.2:8975` repository host. A match is evidence of official-client repository URL persistence; no match is a **test failure**, not an accepted subscription.

The only uploaded result is a bounded JSON receipt with exact source SHA, temporary **public** repository signer fingerprint, private SQLite digest (not its contents) and true/false flags. No publisher private credentials, F-Droid app DB, test APK, real release or owner production signer is uploaded.

## Strict outcome interpretation

If the real hosted Android workflow reports **SUCCESS**, and the log prints `ACTUAL_OFFICIAL_FDROID_NATIVE_REPO_SQLITE_PERSISTENCE_VERIFIED_NOT_APP_INSTALL`, then actual v1/v2 signed-index fetch and native SQLite host persistence are independently accepted on an isolated emulator.

That still does **not** prove that the official client stored the correct repository-signing certificate pin in its DB, downloaded and installed the staged v1 APK, performed an in-client v2 upgrade, enabled unattended update, accepted an authentic public HTTPS repository, or installed anything on the owner's device. These remain explicitly FALSE in the receipt.

The test requires only a short-lived ephemeral test CA, rooted disposable emulator, real signed F-Droid metadata and actual official F-Droid APK. The production public catalog remains empty. If the official APK stores repositories in a non-SQLite backend, the client never commits the repo, or SQLite cannot be read without race/transaction inconsistencies, the test fails; **do not claim persistence or replace evidence with a simulated DB**.

## Exact CI acceptance requirements

The PR source must pass hosted Linux and Windows CI, CodeQL, Trivy and the **actual** `HamApp Real Official F-Droid Client Signed Test Repo Fetch` Android emulator integration job on the exact final PR HEAD. The API is a read-only proof, not an installer, publisher approval or live deployment. On merge, reverify latest main checks and owner-runner status and maintain the integrated gap ledger.

## Actual failed emulator diagnostic and corrective integration — 2026-11-03

Exact prior [real Android CI #41626369937](https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41626369937) **FAILED** after real official signed-index v1 fetch and re-signed v2 staging. The screenshot artifact exposed the root cause of an incomplete UI acceptance: after safely denying the Android 13 F-Droid notification-permission dialog (no new permission granted), the real official **“Add repository”** button was visible and had *not been tapped* at the point the earlier test accepted the first GET; later the screenshot showed **“Adding repository...”** with a spinner, so the client was still processing the addition. The DB snapshot then failed the initial overly tight 48MiB size bound. HTTP requests and a loading indicator are not proof of a committed repository record.

A revised test now selects and taps ONLY the actual clickable `Add repository` node owned by `org.fdroid.fdroid` via real accessibility hierarchy (no hard-coded coordinates or system permission bypass), requires a logged positive tap result, gives the upstream client time to commit its SQLite operation, and then checks real bounded read-only native DB contents. The private SQLite/WAL archive cap is conservatively expanded for the upstream client's default catalog size, with diagnostic size reported without exposing any DB bytes. Full private archive is still destroyed before uploads. Exact final feature-head CI/CodeQL/Trivy AND true Android SQLite proof are required; previous red runs are not accepted.

An untrusted external APK or production repo is never installed; this is a hosted CI-only ephemeral official-client repository-enrollment acceptance candidate.
