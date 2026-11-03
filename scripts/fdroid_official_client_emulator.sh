#!/usr/bin/env bash
# Official F-Droid Android client authenticity and actual isolated emulator intent acceptance.
# NEVER deploy a repository, auto-confirm installer permissions or touch owner devices.
set -euo pipefail
[[ "${GITHUB_ACTIONS:-}" == "true" ]] || { echo "HOSTED_CI_ONLY" >&2; exit 1; }
out=dist/official-fdroid-client
apk="$RUNNER_TEMP/hamapp-official-fdroid/F-Droid.apk"
expected_gpg=37D2C98789D8311948394E3E41E7044E1DBA2E89
expected_apk_cert=43238d512c1e5eb2d6569f4a3afbf5523418b82e0a3ed1552770abb9a9c9ccab

case "${1:-}" in
  prepare)
    mkdir -p "$RUNNER_TEMP/hamapp-official-fdroid" "$out"
    chmod 700 "$RUNNER_TEMP/hamapp-official-fdroid"
    base="$RUNNER_TEMP/hamapp-official-fdroid"
    mkdir -m 700 "$base/gnupg"
    # Signed official F-Droid Android client; key material is PUBLIC, pinned by
    # separately documented F-Droid GPG fingerprint and APK signer cert identity.
    curl --proto '=https' --tlsv1.2 -fLsS --retry 3 --max-time 180 \
      'https://f-droid.org/F-Droid.apk' -o "$apk"
    curl --proto '=https' --tlsv1.2 -fLsS --retry 3 --max-time 60 \
      'https://f-droid.org/F-Droid.apk.asc' -o "$base/F-Droid.apk.asc"
    curl --proto '=https' --tlsv1.2 -fLsS --retry 3 --max-time 60 \
      'https://raw.githubusercontent.com/f-droid/fdroid-website/master/admin%40f-droid.org.gpg' \
      -o "$base/admin.gpg"
    test -s "$apk" && test -s "$base/F-Droid.apk.asc" && test -s "$base/admin.gpg"
    test "$(stat -c %s "$apk")" -lt 150000000
    gpg --batch --no-tty --homedir "$base/gnupg" --import "$base/admin.gpg" >/dev/null 2>&1
    fingerprint=$(gpg --batch --homedir "$base/gnupg" --with-colons --fingerprint \
      | awk -F: '$1=="fpr" {print $10; exit}')
    test "$fingerprint" = "$expected_gpg" || { echo "OFFICIAL_FDROID_GPG_PIN_MISMATCH" >&2; exit 1; }
    gpg --batch --homedir "$base/gnupg" --verify "$base/F-Droid.apk.asc" "$apk"
    aapt="$ANDROID_HOME/build-tools/35.0.0/aapt"
    apksigner="$ANDROID_HOME/build-tools/35.0.0/apksigner"
    "$aapt" dump badging "$apk" | grep -q "package: name='org.fdroid.fdroid'"
    "$apksigner" verify "$apk"
    actual=$("$apksigner" verify --print-certs "$apk" \
      | sed -n 's/^Signer #1 certificate SHA-256 digest: //p' | head -n 1)
    test "${actual,,}" = "$expected_apk_cert" || { echo "OFFICIAL_FDROID_APK_CERT_MISMATCH" >&2; exit 1; }
    sha256sum "$apk" | cut -d' ' -f1 > "$base/official-apk-sha256"
    echo "OFFICIAL_FDROID_GPG_AND_ANDROID_SIGNER_CRYPTO_VERIFIED"
    ;;
  verify)
    test -s "$apk"
    "$ANDROID_HOME/build-tools/35.0.0/apksigner" verify "$apk"
    adb wait-for-device
    adb install -r "$apk" | grep -F 'Success'
    adb shell pm path org.fdroid.fdroid | grep -F 'package:'
    # Use official APK's exported launcher resolution; the version-specific
    # Java activity class is not a stable exported CLI contract.
    if ! adb shell monkey -p org.fdroid.fdroid -c android.intent.category.LAUNCHER 1 > "$RUNNER_TEMP/fdroid-launch.txt" 2>&1; then
      echo "OFFICIAL_FDROID_LAUNCH_FAILED" >&2
      cat "$RUNNER_TEMP/fdroid-launch.txt" >&2
      exit 1
    fi
    grep -Fq 'Events injected: 1' "$RUNNER_TEMP/fdroid-launch.txt"
    echo "OFFICIAL_FDROID_LAUNCHER_EVENT_ACCEPTED"
    # Use the REAL officially signed F-Droid app as the intent target. The
    # deliberately untrusted *.invalid URL is NOT added as a repository.
    dummy="fdroidrepos://https://example.invalid/fdroid/repo/?fingerprint=AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    if ! adb shell am start -W -a android.intent.action.VIEW \
      -c android.intent.category.BROWSABLE \
      -p org.fdroid.fdroid -d "$dummy" > "$RUNNER_TEMP/fdroid-repo-intent.txt" 2>&1; then
      echo "OFFICIAL_FDROID_REPO_INTENT_DISPATCH_REJECTED" >&2
      cat "$RUNNER_TEMP/fdroid-repo-intent.txt" >&2
      exit 1
    fi
    if ! grep -Fq 'Status: ok' "$RUNNER_TEMP/fdroid-repo-intent.txt"; then
      echo "OFFICIAL_FDROID_REPO_INTENT_DID_NOT_LAUNCH" >&2
      cat "$RUNNER_TEMP/fdroid-repo-intent.txt" >&2
      exit 1
    fi
    adb shell dumpsys activity activities > "$RUNNER_TEMP/fdroid-activities.txt"
    grep -Fq 'org.fdroid.fdroid' "$RUNNER_TEMP/fdroid-activities.txt"
    mkdir -p "$out"
    # Android UIAutomator can return a null root node for this official
    # upstream APK on emulators. Do not pretend a UI dump was verified;
    # assert the real app process and real ACTION_VIEW dispatch instead.
    adb shell pidof org.fdroid.fdroid | grep -Eq '^[0-9]+( [0-9]+)*$'
    adb exec-out screencap -p > "$out/client-intent.png"
    test "$(stat -c %s "$out/client-intent.png")" -gt 1000
    ui_ok=false
    for attempt in 1 3; do
      if adb shell uiautomator dump /sdcard/fdroid-client.xml > "$RUNNER_TEMP/fdroid-ui-attempt.txt" 2>&1 \
         && adb pull /sdcard/fdroid-client.xml "$out/ui.xml" >/dev/null 2>&1 \
         && grep -Fq 'package="org.fdroid.fdroid"' "$out/ui.xml"; then
        ui_ok=true
        break
      fi
      sleep 2
    done
    echo "OFFICIAL_FDROID_APK_INSTALLED_PROCESS_ALIVE_AND_INTENT_DISPATCHED; UI_DUMP_VERIFIED=$ui_ok"
    FDROID_UI_VERIFIED="$ui_ok" python3 - <<'PY'
import hashlib, json, os
from pathlib import Path
apk=Path(os.environ["RUNNER_TEMP"])/"hamapp-official-fdroid/F-Droid.apk"
receipt={
"schema_version":1,
"scope":"official-F-Droid-signed-client-emulator-intent-only",
"official_gpg_primary_fingerprint_pinned":True,
"official_apk_cert_fingerprint_pinned":True,
"official_apk_sha256":hashlib.sha256(apk.read_bytes()).hexdigest(),
"real_emulator_official_fdroid_apk_installed":True,
"real_fdroidrepos_intent_activity_launched":True,
"official_fdroid_process_alive_after_intent":True,
"ui_hierarchy_verified":os.environ.get("FDROID_UI_VERIFIED") == "true",
"example_invalid_repository_added":False,
"owner_repo_subscription_verified":False,
"official_client_app_install_or_update_verified":False,
"production_smartphone_acceptance":False,
"production_ready":False
}
p=Path("dist/official-fdroid-client/receipt.json")
p.write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n",encoding="utf-8")
PY
    echo "OFFICIAL_FDROID_ANDROID_EMULATOR_INTENT_ROUTING_ACCEPTED_NOT_REPO_SUBSCRIPTION"
    ;;
  *)
    echo "usage: $0 prepare|verify" >&2
    exit 2
    ;;
esac
