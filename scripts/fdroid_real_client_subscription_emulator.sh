#!/usr/bin/env bash
# Isolated *real upstream* F-Droid client + signed throwaway repository trial.
# Not an owner/publisher cert, not production and never a real owner device.
set -euo pipefail
test "${GITHUB_ACTIONS:-}" = true
test "${RUNNER_OS:-}" = Linux
base="$RUNNER_TEMP/hamapp-fdroid-real-official-client-lab"
state="$base/state.json"
request_log="$base/requests.jsonl"
out=dist/fdroid-real-client-probe
mkdir -p "$out"
test -s "$state"
test -s "$RUNNER_TEMP/hamapp-official-fdroid/F-Droid.apk"
fp=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["fingerprint"])' "$state")
[[ "$fp" =~ ^[A-Fa-f0-9]{64}$ ]]
# Real host HTTP is visible ONLY to this disposable Android emulator on
# 10.0.2.2. The filesystem webroot contains signed files, never config.yml.
python3 scripts/fdroid_client_private_repo_server.py > "$base/http-server-private.log" 2>&1 &
server_pid=$!
trap 'kill "$server_pid" 2>/dev/null || true; wait "$server_pid" 2>/dev/null || true; rm -rf "$base" "$RUNNER_TEMP/hamapp-official-fdroid" dist/android-two-version' EXIT

ready=false
for t in $(seq 1 24); do
  if curl -fsS --max-time 2 "http://127.0.0.1:8975/fdroid/repo/index-v2.json" -o "$base/host-index-check.json"; then
    ready=true
    break
  fi
  sleep 1
done
test "$ready" = true
# Keep this host curl DISTINCT from F-Droid client requests in the observed log.
: > "$request_log"
adb wait-for-device
adb install -r "$RUNNER_TEMP/hamapp-official-fdroid/F-Droid.apk" | grep -F Success
adb shell pm path org.fdroid.fdroid | grep -F package:
adb shell monkey -p org.fdroid.fdroid -c android.intent.category.LAUNCHER 1 >/dev/null
sleep 4
# fdroidrepo:// is the official HTTP emulator-only deep-link. HTTPS production
# uses fdroidrepos://. NEVER embed 'http://' after fdroidrepo://.
uri="fdroidrepo://10.0.2.2:8975/fdroid/repo/?fingerprint=$fp"
adb shell am start -W -a android.intent.action.VIEW \
  -c android.intent.category.BROWSABLE -p org.fdroid.fdroid -d "$uri" > "$base/intent-private.txt"
grep -Fq 'Status: ok' "$base/intent-private.txt"
echo "OFFICIAL_FDROID_REAL_SIGNED_REPO_ADD_INTENT_SENT"
request_count() {
  python3 - "$request_log" <<'PY'
import json,sys
try:
    lines=open(sys.argv[1],encoding="utf-8").read().splitlines()
    events=[json.loads(line) for line in lines if line]
    print(sum(1 for event in events
      if event.get("method")=="GET"
      and event.get("path") in ("/fdroid/repo/index-v2.json","/fdroid/repo/entry.jar","/fdroid/repo/index.jar")
      and "curl" not in event.get("agent","").lower()
      and "python" not in event.get("agent","").lower()))
except (ValueError,OSError):
    print(0)
PY
}
click_actual_accessible_control() {
  if adb shell uiautomator dump /sdcard/hamapp-fdroid-live.xml > "$base/uiauto-private.txt" 2>&1 \
    && adb pull /sdcard/hamapp-fdroid-live.xml "$base/window.xml" >/dev/null 2>&1; then
    local point
    point=$(python3 scripts/fdroid_client_accessible_ui.py --xml "$base/window.xml") || return 0
    local x y
    read -r x y <<< "$point"
    if [[ "$x" =~ ^[0-9]+$ && "$y" =~ ^[0-9]+$ ]]; then
      adb shell input tap "$x" "$y"
    fi
  fi
}
found=false
for n in $(seq 1 24); do
  click_actual_accessible_control
  sleep 3
  if [ "$(request_count)" -ge 1 ]; then
    found=true
    break
  fi
done
adb exec-out screencap -p > "$out/official-client-after-repo-intent.png" || true
if [ "$found" != true ]; then
  echo "OFFICIAL_FDROID_CLIENT_DID_NOT_FETCH_SIGNED_REPO_FROM_EMULATOR" >&2
  exit 1
fi
v1_sha=$(sha256sum "$base/webroot/fdroid/repo/index-v2.json" | awk '{print $1}')
echo "OFFICIAL_FDROID_REAL_TEST_SIGNED_INDEX_V1_REQUEST_OBSERVED"
# Re-sign actual index with same throwaway repository key after placing
# actual higher-version APK, and force the UI refresh on the emulator.
python3 scripts/fdroid_client_private_repo_lab.py --version 2 \
  --apk dist/android-two-version/v2.apk --source-sha "$GITHUB_SHA"
v2_sha=$(sha256sum "$base/webroot/fdroid/repo/index-v2.json" | awk '{print $1}')
test "$v1_sha" != "$v2_sha"
: > "$request_log"
adb shell am start -W -a android.intent.action.VIEW \
  -c android.intent.category.BROWSABLE -p org.fdroid.fdroid -d "$uri" > "$base/v2-intent-private.txt"
for n in $(seq 1 24); do
  click_actual_accessible_control
  sleep 3
  if [ "$(request_count)" -ge 1 ]; then
    break
  fi
done
adb exec-out screencap -p > "$out/official-client-after-index-v2.png" || true
v2_seen=false
if [ "$(request_count)" -ge 1 ]; then v2_seen=true; fi
if [ "$v2_seen" != true ]; then
  echo "OFFICIAL_FDROID_CLIENT_DID_NOT_FETCH_UPDATED_SIGNED_INDEX" >&2
  exit 1
fi
FDROID_LAB="$base" FDROID_INDEX_V1="$v1_sha" FDROID_INDEX_V2="$v2_sha" python3 - <<'PY'
import hashlib,json,os
from pathlib import Path
base=Path(os.environ["FDROID_LAB"])
state=json.loads((base/"state.json").read_text("utf-8"))
assert len(state["versions"])==2
receipt={
"schema_version":1,
"scope":"actual-official-fdroid-client-signed-throwaway-repo-emulator-index-requests",
"source_sha":state["source_sha"],
"real_official_fdroid_client_apk_installed":True,
"disposable_signed_repo_fingerprint_verified":True,
"real_two_signed_indexes_same_disposable_key":True,
"real_version_codes":[p["version_code"] for p in state["versions"]],
"real_v1_index_sha256":os.environ["FDROID_INDEX_V1"],
"real_v2_index_sha256":os.environ["FDROID_INDEX_V2"],
"real_client_v1_signed_index_http_request_observed":True,
"real_client_v2_signed_index_http_request_observed":True,
"official_client_repository_persisted_in_database_verified":False,
"actual_fdroid_client_app_install_verified":False,
"actual_fdroid_client_app_upgrade_verified":False,
"owner_key_or_device_verified":False,
"public_release_authorized":False,
"production_ready":False
}
Path("dist/fdroid-real-client-probe/receipt.json").write_text(
 json.dumps(receipt,sort_keys=True,indent=2)+"\n",encoding="utf-8")
PY
echo "ACTUAL_FDROID_CLIENT_SIGNED_INDEX_V1_V2_REQUESTS_OBSERVED; INSTALL_AND_SUBSCRIPTION_DB_NOT_VERIFIED"
