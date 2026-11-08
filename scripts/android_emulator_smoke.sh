#!/usr/bin/env bash
set -euo pipefail
python3 scripts/build_android_catalog.py
gradle --no-daemon -p android :app:assembleDebug
apk=android/app/build/outputs/apk/debug/app-debug.apk
test -s "$apk"
adb wait-for-device
adb shell getprop sys.boot_completed
adb install -r "$apk"
adb shell pm list packages | grep -F 'package:ir.hamapp.store'
# Android 35 Google APIs can briefly overlay the launcher (first-run
# permission, keyguard or rendering transition) after Activity reports OK.
# Do not treat a transient accessibility dump as the app's actual UI.
adb shell input keyevent 224 || true
adb shell wm dismiss-keyguard || true
mkdir -p dist/android-emulator
accepted=0
for attempt in 1 2 3 4 5; do
  adb shell am force-stop ir.hamapp.store || true
  adb shell am start -W -n ir.hamapp.store/.MainActivity | tee android-activity-launch.txt
  grep -q 'Status: ok' android-activity-launch.txt
  sleep 2
  adb shell uiautomator dump /sdcard/hamapp-window.xml || true
  adb pull /sdcard/hamapp-window.xml dist/android-emulator/window.xml || true

  # The owner-approved cards are below the compact store controls on smaller
  # devices. Capture the actual scrolled ScrollView rather than weakening the
  # fail-closed requirement for unapproved install actions.
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
  adb shell uiautomator dump /sdcard/hamapp-scrolled.xml || true
  adb pull /sdcard/hamapp-scrolled.xml dist/android-emulator/scrolled.xml || true
  if python3 scripts/check_android_emulator_ui.py \
     dist/android-emulator/window.xml dist/android-emulator/scrolled.xml; then
    accepted=1
    break
  fi
  echo "ANDROID_UI_SNAPSHOT_RETRY=${attempt}/5" >&2
done
adb exec-out screencap -p > dist/android-emulator/screen.png
test -s dist/android-emulator/screen.png
if [[ "$accepted" -ne 1 ]]; then
  echo "NATIVE_ANDROID_PREVIEW_UI_STRICT_ACCEPTANCE_FAILED" >&2
  exit 1
fi
echo "NATIVE_ANDROID_PREVIEW_LAUNCHED; UNAPPROVED_INSTALL_ACTION_DISABLED"
# Exercise actual Android private preferences and pinned multiple-source trust
# transitions on the already-running ephemeral device, not only source text.
gradle --no-daemon -p android :app:connectedDebugAndroidTest
mkdir -p dist/android-emulator/instrumentation
cp -R android/app/build/outputs/androidTest-results/connected/. dist/android-emulator/instrumentation/
echo "NATIVE_SIGNED_REPOSITORY_LIFECYCLE_INSTRUMENTED_PASS"
