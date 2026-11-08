#!/usr/bin/env bash
set -euo pipefail
test "$GITHUB_ACTIONS" = "true"
out=dist/android-two-version
apk=android/app/build/outputs/apk/debug/app-debug.apk
mkdir -p "$out"
case "$1" in
  prepare)
    python3 scripts/build_android_catalog.py
    gradle --no-daemon -p android :app:assembleDebug
    test -s "$apk"
    cp "$apk" "$out/v1.apk"
    python3 - <<'PY'
from pathlib import Path
p=Path("android/app/build.gradle")
s=p.read_text()
assert s.count("versionCode 1")==1 and s.count("versionName '0.1.0-preview'")==1
p.write_text(s.replace("versionCode 1", "versionCode 2").replace("versionName '0.1.0-preview'", "versionName '0.2.0-preview'"))
PY
    gradle --no-daemon -p android :app:assembleDebug
    test -s "$apk"
    cp "$apk" "$out/v2.apk"
    tools="$ANDROID_HOME/build-tools/35.0.0"
    "$tools/apksigner" verify "$out/v1.apk"
    "$tools/apksigner" verify "$out/v2.apk"
    "$tools/aapt" dump badging "$out/v1.apk" | grep -F "versionCode='1'"
    "$tools/aapt" dump badging "$out/v2.apk" | grep -F "versionCode='2'"
    fp1=$("$tools/apksigner" verify --print-certs "$out/v1.apk" | grep 'Signer #1 certificate SHA-256 digest' | awk '{print $NF}')
    fp2=$("$tools/apksigner" verify --print-certs "$out/v2.apk" | grep 'Signer #1 certificate SHA-256 digest' | awk '{print $NF}')
    test -n "$fp1"
    test "$fp1" = "$fp2"
    # A separately generated, disposable identity must NEVER be allowed to replace v2.
    keytool -genkeypair -noprompt -storetype PKCS12 \
      -keystore "$out/untrusted-ci-only.p12" -alias untrusted \
      -storepass "ephemeral-test-passphrase" -keypass "ephemeral-test-passphrase" \
      -keyalg RSA -keysize 2048 -validity 1 -dname "CN=Untrusted-HamApp-CI-Test"
    "$tools/apksigner" sign --ks "$out/untrusted-ci-only.p12" \
      --ks-key-alias untrusted --ks-pass pass:ephemeral-test-passphrase \
      --key-pass pass:ephemeral-test-passphrase \
      --out "$out/v2-foreign-signer.apk" "$out/v2.apk"
    "$tools/apksigner" verify "$out/v2-foreign-signer.apk"
    other=$("$tools/apksigner" verify --print-certs "$out/v2-foreign-signer.apk" | grep 'Signer #1 certificate SHA-256 digest' | awk '{print $NF}')
    test -n "$other" && test "$other" != "$fp2"
    # A truncated signed archive must fail package integrity checks.
    head -c 4096 "$out/v2.apk" > "$out/v2-truncated.apk"
    if "$tools/apksigner" verify "$out/v2-truncated.apk" >/dev/null 2>&1; then
      echo "SECURITY FAILURE: truncated APK passed signature validation" >&2; exit 1
    fi
    echo "V1_V2_APK_BUILT_SAME_EPHEMERAL_DEBUG_CERT"
    ;;
  verify)
    adb wait-for-device
    adb install -r "$out/v1.apk"
    adb shell dumpsys package ir.hamapp.store | grep -Eq 'versionCode=1([[:space:]]|$)'
    adb install -r "$out/v2.apk"
    adb shell dumpsys package ir.hamapp.store | grep -Eq 'versionCode=2([[:space:]]|$)'
    if adb install -r "$out/v1.apk" > "$out/downgrade-attempt.txt" 2>&1; then
       echo "SECURITY FAILURE: downgrade accepted" >&2
       exit 1
    fi
    grep -Fq 'INSTALL_FAILED_VERSION_DOWNGRADE' "$out/downgrade-attempt.txt"
    adb shell dumpsys package ir.hamapp.store | grep -Eq 'versionCode=2([[:space:]]|$)'
    if adb install -r "$out/v2-foreign-signer.apk" > "$out/foreign-signer-attempt.txt" 2>&1; then
      echo "SECURITY FAILURE: foreign signer was accepted as an update" >&2; exit 1
    fi
    grep -Fq 'INSTALL_FAILED_UPDATE_INCOMPATIBLE' "$out/foreign-signer-attempt.txt"
    adb shell dumpsys package ir.hamapp.store | grep -Eq 'versionCode=2([[:space:]]|$)'
    if adb install -r "$out/v2-truncated.apk" > "$out/truncated-attempt.txt" 2>&1; then
      echo "SECURITY FAILURE: truncated APK was accepted" >&2; exit 1
    fi
    adb shell dumpsys package ir.hamapp.store | grep -Eq 'versionCode=2([[:space:]]|$)'
    # Android 35/Google APIs can leave the keyguard or a transient system
    # overlay in front of the freshly upgraded Activity. A failed accessibility
    # snapshot is NOT evidence that the native app passed. Restart the SAME
    # installed v2 process and require both original and scrolled snapshots.
    # This is the strict already-accepted hosted UI handshake, not a bypass.
    adb shell input keyevent 224 || true
    adb shell wm dismiss-keyguard || true
    accepted=0
    for attempt in 1 2 3 4 5; do
      adb shell am force-stop ir.hamapp.store || true
      adb shell am start -W -n ir.hamapp.store/.MainActivity | tee "$out/activity.txt"
      grep -q 'Status: ok' "$out/activity.txt"
      sleep 2
      # Never reuse a previous failed UI snapshot on a retry.
      rm -f "$out/ui.xml" "$out/scrolled.xml"
      adb shell uiautomator dump /sdcard/hamapp-two-version.xml || true
      adb pull /sdcard/hamapp-two-version.xml "$out/ui.xml" || true

      # Owner-approved app cards are inside a nested ScrollView and may be
      # below the initial viewport. Do NOT relax the disabled-install guard.
      dimensions=$(adb shell wm size | grep -Eo '[0-9]+x[0-9]+' | tail -1)
      width=${dimensions%x*}
      height=${dimensions#*x}
      if [[ -z "$width" || -z "$height" || "$width" == "$height" ]]; then
        echo "ANDROID_DISPLAY_DIMENSIONS_INVALID" >&2
        exit 1
      fi
      x=$((width / 2))
      y1=$((height * 86 / 100))
      y2=$((height * 52 / 100))
      adb shell input swipe "$x" "$y1" "$x" "$y2" 380
      adb shell input swipe "$x" "$y1" "$x" "$y2" 380
      sleep 1
      adb shell uiautomator dump /sdcard/hamapp-two-version-scrolled.xml || true
      adb pull /sdcard/hamapp-two-version-scrolled.xml "$out/scrolled.xml" || true
      if python3 scripts/check_android_emulator_ui.py "$out/ui.xml" "$out/scrolled.xml"; then
        accepted=1
        break
      fi
      echo "ANDROID_UPGRADED_UI_CAPTURE_RETRY=${attempt}/5" >&2
    done
    if [[ "$accepted" -ne 1 ]]; then
      echo "ACTUAL_UPGRADED_UI_VALIDATION_FAILED" >&2
      exit 1
    fi
    adb exec-out screencap -p > "$out/after-update.png"
    test -s "$out/after-update.png"
    python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path("dist/android-two-version")
v1=hashlib.sha256((p/"v1.apk").read_bytes()).hexdigest()
v2=hashlib.sha256((p/"v2.apk").read_bytes()).hexdigest()
assert v1!=v2
receipt={"schema_version":1,"scope":"isolated-android-emulator-debug-upgrade","package":"ir.hamapp.store",
"version_codes":[1,2],"same_debug_signer":True,"apk_v1_sha256":v1,"apk_v2_sha256":v2,
"real_emulator_upgrade_passed":True,"default_downgrade_rejected":True,"foreign_signer_update_rejected":True,
"corrupt_package_update_rejected":True,"installed_v2_preserved_after_denials":True,
"native_ui_after_upgrade":True,
"unapproved_FDroid_install_control_disabled":True,
"production_signer_verified":False,"fdroid_signed_repo_subscription_verified":False,
"owner_device_upgrade_verified":False,"production_ready":False}
(p/"report.json").write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
PY
    rm -f "$out/v1.apk" "$out/v2.apk" "$out/v2-foreign-signer.apk" \
      "$out/v2-truncated.apk" "$out/untrusted-ci-only.p12" \
      "$out/downgrade-attempt.txt" "$out/foreign-signer-attempt.txt" \
      "$out/truncated-attempt.txt"
    echo "REAL_ANDROID_DEBUG_UPGRADE_DOWNGRADE_SIGNER_AND_CORRUPTION_CHECKS_ACCEPTED"
    ;;
  *) echo "usage: $0 prepare|verify" >&2; exit 2 ;;
esac
