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
adb shell am force-stop ir.hamapp.store || true
adb shell am start -W -n ir.hamapp.store/.MainActivity | tee android-activity-launch.txt
grep -q 'Status: ok' android-activity-launch.txt
mkdir -p dist/android-emulator
adb shell uiautomator dump /sdcard/hamapp-window.xml
adb pull /sdcard/hamapp-window.xml dist/android-emulator/window.xml
python3 scripts/check_android_emulator_ui.py dist/android-emulator/window.xml
adb exec-out screencap -p > dist/android-emulator/screen.png
test -s dist/android-emulator/screen.png
echo "NATIVE_ANDROID_PREVIEW_LAUNCHED; INSTALL_ACTION_DISABLED"
