# Android two-version native upgrade — real emulator, debug signatures

The hosted GitHub workflow builds two **actual debug-signed** APKs of HamApp from the same source, with versionCode 1 / 0.1.0-preview and 2 / 0.2.0-preview. Version metadata is modified only in the ephemeral CI checkout; the repository's production code stays unchanged.

The test verifies same APK signing-certificate fingerprint, installs v1 on a real Android 35 emulator, upgrades to v2 through Android Package Manager, then attempts a downgrade without any security override and expects Android's INSTALL_FAILED_VERSION_DOWNGRADE. After the upgrade it launches the native RTL Persian UI and validates the F-Droid install button remains disabled; screenshot and receipt are saved.

**No APK, keystore or secret is uploaded.** The two debug APKs and device logs that could contain installation details are deleted after the test. Output is only short-lived proof of the test and UI screenshot, with all production approval fields set false.

This confirms Android native version-code upgrade mechanics and rejection of a downgrade under an ephemeral debug signer, NOT real F-Droid signed-repository subscription, developer APK certificate validation, stable production app signing, actual publisher app updates or installation on an owner's device. Requires independent real signed release gates before any public install is enabled.

Acceptance requires a genuine successful GitHub Action run for .github/workflows/android-two-version-smoke.yml.
