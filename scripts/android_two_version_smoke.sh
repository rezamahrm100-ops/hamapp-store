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
    adb shell am force-stop ir.hamapp.store || true
    adb shell am start -W -n ir.hamapp.store/.MainActivity | tee "$out/activity.txt"
    grep -q 'Status: ok' "$out/activity.txt"
    adb shell uiautomator dump /sdcard/hamapp-two-version.xml
    adb pull /sdcard/hamapp-two-version.xml "$out/ui.xml"
    python3 scripts/check_android_emulator_ui.py "$out/ui.xml"
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
"real_emulator_upgrade_passed":True,"default_downgrade_rejected":True,"native_ui_after_upgrade":True,
"unapproved_FDroid_install_control_disabled":True,
"production_signer_verified":False,"fdroid_signed_repo_subscription_verified":False,
"owner_device_upgrade_verified":False,"production_ready":False}
(p/"report.json").write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
PY
    rm -f "$out/v1.apk" "$out/v2.apk" "$out/downgrade-attempt.txt"
    echo "REAL_ANDROID_DEBUG_UPGRADE_AND_DOWNGRADE_REJECTION_ACCEPTED"
    ;;
  *) echo "usage: $0 prepare|verify" >&2; exit 2 ;;
esac
