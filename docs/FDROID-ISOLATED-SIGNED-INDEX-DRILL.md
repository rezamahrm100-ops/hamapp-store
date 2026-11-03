# Isolated F-Droid signed-index-v2 integration drill

This workflow uses the **official fdroidserver 2.4.5 in an isolated Python virtual environment, with Androguard 4.1.4**, not a custom signature implementation. Its test runs on a GitHub-hosted ephemeral Ubuntu 24.04 runner, only for reviewed main or manual dispatch of main.

1. Builds the actual HamApp native Android *debug* APK from the current checkout with the existing AGP/Gradle toolchain.
2. Uses `fdroid init` in an isolated temporary workspace, with a distinct disposable HOME, to generate a *throwaway* signing key and private config.
3. Uses `fdroid update --create-metadata` on the debug APK to generate a real signed index-v2 entry.
4. Serves that repository **only on 127.0.0.1** in the same ephemeral runner; no public endpoint or publishing credentials are involved.
5. Extracts the temporary signing fingerprint via upstream fdroidserver's JAR certificate parser. Uses `fdroidserver.index.download_repo_index_v2(..., verify_fingerprint=True)` to verify the actual index and check that `ir.hamapp.store` is present.
6. Repeats verification with a wrong pinned fingerprint and a tampered index-v2.json. Both MUST be rejected.
7. Destroys the test keystore/config and server before uploading anything. The only artifact is a **receipt JSON** asserting non-production status; no APK, private key, signed index, temporary config or passwords are ever uploaded or checked into the public repository.

The fingerprint is derived from the same ephemeral test keystore and is NOT independently trusted. This validates that the official signing and verification pipeline actually works; it does **not** validate your production signing identity, a persistent key, HTTPS public hosting, official F-Droid client subscription, an app installation/update, or any publisher's release key.

This work deliberately does not change catalog/android_repository.json (still null), trusted_signers.json (empty), release_history.json (empty), or the public catalogue's disabled download buttons.

**Acceptance:** the actual GitHub Actions run must show all steps successful and the named review receipt artifact. A green Python unittest suite alone is not sufficient.

Upstream guidance: https://f-droid.org/docs/Setup_an_F-Droid_App_Repo/ . Keep real production signing on a separate owner-controlled system with independent offline backups; never transport signing secrets through public Actions.

## Toolchain compatibility fix

The first hosted execution failed in Ubuntu's older fdroidserver/Androguard package at APK resources.arsc parsing. The dedicated isolated test now pins fdroidserver==2.4.5 and androguard==4.1.4 inside a temporary venv. This is not a production signer and does not transfer a signing key. Validate the new GitHub run before claiming a successful real signed-index drill.

## Library initialization repair

The next real hosted run using fdroidserver 2.4.5 correctly built the signed index, but direct Python index verification required `fdroidserver.common.config` and the installed `jarsigner` path to be initialized from the temporary workspace's config.yml. The integration script now loads this configuration inside the disposable test process before calling the official index-v2 verifier. No config or key is uploaded or used for production.

## Actual two-version signed F-Droid index continuity — 2026-11-03

The hosted integration now builds **two real Android DEBUG APK versions** (`versionCode 1` and `2`) with one disposable Android debug signing identity, reusing `scripts/android_two_version_smoke.sh prepare`. In the same isolated upstream `fdroidserver==2.4.5` workspace, the test signs an index containing v1, verifies actual `entry.jar` and exact APK bytes, then adds the second real APK and runs `fdroid update --create-metadata` again. It rejects an unchanged index, any change to the F-Droid repository certificate, disappearance of v1, missing v2, APK SHA/version/size substitution and wrong key/tampered index. Both versions are checked using upstream JAR certificate verification and unique exact candidate matching, not inferred from test JSON.

The test outputs a strictly whitelisted, no-secret receipt. The report explicitly marks `official_fdroid_client_subscribed=false`, `two_version_client_update_performed=false` and `real_owner_key_restored_or_backed_up=false`. The isolated test key is temporary; two signed indices with the same temporary key **do not** prove persistence across devices, actual offline backup/restore, owner public HTTPS origin or an F-Droid Android client performing an install/update. Actual workflow SHA and SUCCESS are mandatory before claiming acceptance.

To run the complete source/real-artifact workflow on a hosted isolated runner, use `.github/workflows/fdroid-signed-index-drill.yml`. It produces disposable APKs/keys locally on GitHub, deletes them before uploading a short-lived JSON acceptance receipt, and never modifies public approved trust registries.
