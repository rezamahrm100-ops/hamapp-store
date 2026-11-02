# HamApp Android native client — preview and F-Droid handoff

This is a **native Java Android application** (not a WebView wrapper). It displays an offline, RTL Persian catalogue and delegates installation/update to the existing GPL-3.0 F-Droid Android client. This deliberately reuses upstream installer infrastructure without copying, modifying or redistributing F-Droid source at this point. Upstream client: https://gitlab.com/fdroid/fdroidclient (GPL-3.0-or-later). Official subscription procedure: https://f-droid.org/docs/Setup_an_F-Droid_App_Repo/

## Build system
- Android Gradle Plugin `8.13.0`, Gradle `8.13`, JDK 17, Android SDK 35.
- Source under `android/` uses platform APIs only (no third-party runtime dependencies), minSdk 26, targetSdk 35.
- GitHub-hosted Ubuntu workflow `.github/workflows/android-client-preview.yml` tests Python approval gates, builds a Debug APK, runs lint and verifies the APK's **debug certificate only** with apksigner.
- Output is a three-day GitHub Actions artifact, never a public production release.
- The debug key is ephemeral; uninstalling a preview may be necessary before using a differently signed build. Never register the debug signing certificate as a publisher identity.

## Catalogue and trust contract
- `scripts/build_android_catalog.py` only creates an Android asset snapshot after validating the existing `catalog/apps.json`, `trusted_signers.json`, and `release_history.json`.
- `catalog/android_repository.json` starts as `{"schema_version":1,"repository":null}`. No repository is considered signed or ready at this stage.
- For future registration, use an owner-reviewed canonical HTTPS `https://host.example/fdroid/repo/` and its independently verified 64-character repository signing **fingerprint**. A metadata field alone does NOT verify the signed index, prove ownership or establish consent.
- Even if the repository becomes configured, the catalogue has to contain an independently approved Android release before its F-Droid handoff button can be enabled.
- The F-Droid client receives an ACTION_VIEW URI with explicit fingerprint query and retains final approval/installation prompts. HamApp never requests REQUEST_INSTALL_PACKAGES, runs a silent installer or bypasses Android permissions.
- There are no real approved apps at present; all actions remain disabled.

## Scope and missing production acceptance
1. **Independent F-Droid source reuse**: current solution reuses existing F-Droid *as a companion*; it is NOT a full fork/rebrand of the GPL client and does not claim an integrated app manager.
2. Independently audited repository signing, stable signing key and backup, verified signed index, source provenance, publisher certificate identity and real release.
3. GUI and F-Droid intent handoff on actual Android device/emulator, plus two-version signed installation/update tests.
4. Production APK signing via secure owner-controlled signing environment and stable release key. Play Store/App distribution policy and full accessibility validation before general release.

Manual developer command, not required for owner:
```bash
python3 scripts/build_android_catalog.py
gradle -p android :app:assembleDebug :app:lintDebug
```

The GitHub-hosted workflow performs this without changes to the owner's PC. Source is public, but private application repositories, signing credentials and release APKs stay separate.

## Hosted emulator UI acceptance

`reactivecircus/android-emulator-runner@v2` boots an isolated Android 35 emulator on GitHub-hosted Linux and executes `scripts/android_emulator_smoke.sh`. The test installs the DEBUG APK with ADB, launches the native activity, checks the accessibility hierarchy for a Persian HamApp title, planned-app status and disabled F-Droid install buttons, then stores an emulator screenshot and hierarchy as three-day artifacts. The UI hierarchy parser has negative unit tests. This is a meaningful native-activity smoke test, **not** a test of production F-Droid subscription, binary signatures, updates or physical-device behavior. Do not run it on the owner's Windows session or accept untrusted PR code on the owner runner.
