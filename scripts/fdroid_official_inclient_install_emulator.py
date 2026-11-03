#!/usr/bin/env python3
"""Real F-Droid UI->network->Android PackageManager APK lifecycle in disposable CI.

This uses only live accessibility controls from the upstream official client,
not ADB install, fake SQL inserts, shell PM install, synthetic receipts or
physical owner hardware. Android installer prompts are clicked only when their
actual package-owned UI names the test app. Unknown-source permission settings
are NEVER auto-granted. A failure is a genuine unaccepted integration blocker.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET

from fdroid_official_install_ui import select

APP_PACKAGE = "ir.hamapp.store"
FDROID_PACKAGE = "org.fdroid.fdroid"
INDEX_ROOT = "/fdroid/repo/"
SHA40 = re.compile(r"[a-f0-9]{40}\Z")
APK_FP = re.compile(r"Signer #1 certificate SHA-256 digest:\s*([a-f0-9]{64})", re.I)


class ClientInstallFailure(ValueError):
    pass


def invoke(argv, *, limit=30, required=True):
    p = subprocess.run(argv, capture_output=True, text=True, timeout=limit,
                       check=False)
    if required and p.returncode:
        raise ClientInstallFailure(f"test command {argv[0]} failed (exit {p.returncode})")
    return p.stdout if p.returncode == 0 else ""


def dump_ui(private):
    try:
        invoke(["adb", "shell", "uiautomator", "dump",
                "/sdcard/hamapp-official-install-live.xml"], limit=30)
        invoke(["adb", "pull", "/sdcard/hamapp-official-install-live.xml",
                str(private / "live.xml")], limit=30)
    except (ClientInstallFailure, subprocess.TimeoutExpired):
        return None
    return private / "live.xml"


def tap_from_real_ui(xml, action):
    if not xml:
        return False
    try:
        point = select(xml, action)
    except (OSError, ValueError):
        return False
    if point is None:
        return False
    invoke(["adb", "shell", "input", "tap", str(point[0]), str(point[1])],
           limit=15)
    return True


def installed_version():
    output = invoke(["adb", "shell", "dumpsys", "package", APP_PACKAGE],
                    required=False)
    # Android 33 versionCode appears in the Package record. Not merely
    # observing a F-Droid network request or package details preview.
    codes = re.findall(r"\bversionCode=(\d+)\b", output)
    return int(codes[0]) if codes else None


def count_client_apk_get(path, basename):
    try:
        events = [json.loads(line) for line in path.read_text("utf-8").splitlines() if line]
    except (OSError, ValueError):
        return 0
    return sum(
        event.get("method") == "GET"
        and event.get("path") == INDEX_ROOT + basename
        and "curl" not in str(event.get("agent", "")).lower()
        and "python" not in str(event.get("agent", "")).lower()
        for event in events
    )


def cert_fingerprint(apk):
    output = invoke(["apksigner", "verify", "--print-certs", str(apk)], limit=35)
    match = APK_FP.search(output)
    if not match:
        raise ClientInstallFailure("no verified APK certificate from apksigner")
    return match.group(1).lower()


def verify_installed_apk(version, reference, private):
    actual_version = installed_version()
    if actual_version != version:
        raise ClientInstallFailure("Android PackageManager did not install expected version")
    path_output = invoke(["adb", "shell", "pm", "path", APP_PACKAGE])
    paths = [line[len("package:"):].strip() for line in path_output.splitlines()
             if line.startswith("package:")]
    if len(paths) != 1 or not paths[0].startswith("/data/app/") or not paths[0].endswith(".apk"):
        raise ClientInstallFailure("single native installed Android APK path required")
    copied = private / f"package-v{version}-readback.apk"
    invoke(["adb", "pull", paths[0], str(copied)], limit=60)
    if not copied.is_file() or copied.is_symlink():
        raise ClientInstallFailure("native installed APK readback missing")
    readback_digest = hashlib.sha256(copied.read_bytes()).hexdigest()
    reference_digest = hashlib.sha256(reference.read_bytes()).hexdigest()
    if readback_digest != reference_digest:
        raise ClientInstallFailure("installed bytes differ from independently built signed APK")
    if cert_fingerprint(copied) != cert_fingerprint(reference):
        raise ClientInstallFailure("installed signer differs from expected test APK signer")
    return reference_digest


def run(stage):
    if (os.name != "posix" or os.environ.get("GITHUB_ACTIONS") != "true"
            or os.environ.get("RUNNER_OS") != "Linux"
            or os.environ.get("GITHUB_REPOSITORY") != "rezamahrm100-ops/hamapp-store"):
        raise ClientInstallFailure("real isolated GitHub-hosted Linux Android test only")
    source_sha = os.environ.get("GITHUB_SHA", "")
    if not SHA40.fullmatch(source_sha):
        raise ClientInstallFailure("test source commit SHA is not immutable")
    runner = Path(os.environ["RUNNER_TEMP"]).resolve(strict=True)
    base = runner / "hamapp-fdroid-real-official-client-lab"
    state = json.loads((base / "state.json").read_text("utf-8"))
    if (state.get("source_sha") != source_sha
            or len(state.get("versions", [])) != stage):
        raise ClientInstallFailure("real signed index stage not available")
    reference = Path(f"dist/android-two-version/v{stage}.apk")
    if not reference.is_file():
        raise ClientInstallFailure("real CI-built Android signed APK missing")
    output = Path("dist/fdroid-real-client-probe")
    proof = output / f"official-inclient-installed-v{stage}.json"
    if proof.exists() or proof.is_symlink():
        raise ClientInstallFailure("refuse to overwrite native installation evidence")
    if stage == 1 and installed_version() is not None:
        raise ClientInstallFailure("v1 must be installed by official client, not ADB/preinstall")
    if stage == 2:
        previous = json.loads((output / "official-inclient-installed-v1.json").read_text("utf-8"))
        if (previous.get("real_official_client_app_installed") is not True
                or previous.get("source_sha") != source_sha
                or previous.get("actual_installed_version_code") != 1
                or installed_version() != 1):
            raise ClientInstallFailure("real in-client v1 installation must precede update")
    # Official upstream F-Droid manifest + router accept market://details.
    intent = invoke(["adb", "shell", "am", "start", "-W",
                     "-a", "android.intent.action.VIEW",
                     "-c", "android.intent.category.BROWSABLE",
                     "-p", FDROID_PACKAGE,
                     "-d", f"market://details?id={APP_PACKAGE}"], limit=35)
    if "Status: ok" not in intent:
        raise ClientInstallFailure("official F-Droid app details market intent not accepted")

    clicked_client_button = False
    clicked_system_prompt = False
    with tempfile.TemporaryDirectory(prefix="hamapp-official-client-package-", dir=runner) as tmp:
        private = Path(tmp)
        # A genuine F-Droid app action and actual Android PM readback are both
        # necessary. Only live package-labelled accessibility XML is tapped.
        for attempt in range(42):
            xml = dump_ui(private)
            if xml and tap_from_real_ui(xml, "dismiss-hint"):
                time.sleep(1)
                continue
            if xml and tap_from_real_ui(xml, "confirm-installer"):
                clicked_system_prompt = True
            elif xml and not clicked_client_button and tap_from_real_ui(
                    xml, "install" if stage == 1 else "update"):
                clicked_client_button = True
            if clicked_client_button and installed_version() == stage:
                if count_client_apk_get(base / "requests.jsonl",
                                        f"hamapp-v{stage}.apk") < 1:
                    raise ClientInstallFailure("no real F-Droid client signed APK download request")
                readback_hash = verify_installed_apk(stage, reference, private)
                receipt = {
                    "schema_version": 1,
                    "scope": "hosted-official-F-Droid-app-UI-APK-network-Android-package-manager",
                    "source_sha": source_sha,
                    "package_name": APP_PACKAGE,
                    "real_official_client_app_action_tapped": clicked_client_button,
                    "real_android_installer_confirmation_tapped_if_visible": clicked_system_prompt,
                    "actual_client_apk_get_observed": True,
                    "actual_installed_version_code": stage,
                    "actual_native_installed_apk_bytes_match_ci_built_signed_apk": True,
                    "actual_installed_apk_sha256": readback_hash,
                    "actual_native_signer_matches_ci_built_apk": True,
                    "real_official_client_app_installed": stage == 1,
                    "real_official_client_app_updated": stage == 2,
                    "unknown_source_permission_auto_granted": False,
                    "owner_device_or_production_signer_verified": False,
                    "public_release_authorized": False,
                }
                output.mkdir(parents=True, exist_ok=True)
                proof.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                                 encoding="utf-8")
                print(f"ACTUAL_OFFICIAL_FDROID_UI_NETWORK_NATIVE_PACKAGE_V{stage}_VERIFIED")
                return
            time.sleep(2)
        # Failure evidence from the disposable hosted emulator ONLY, never an
        # owner device or complete unredacted Android settings dump. Record a
        # bounded screenshot and boolean UI predicates, not arbitrary XML,
        # package databases, repo private keys, tokens or test APKs.
        output.mkdir(parents=True, exist_ok=True)
        raw = subprocess.run(["adb", "exec-out", "screencap", "-p"],
                             capture_output=True, timeout=20, check=False)
        if raw.returncode == 0 and raw.stdout.startswith(b"\\x89PNG\\r\\n\\x1a\\n"):
            (output / f"official-inclient-blocker-v{stage}.png").write_bytes(raw.stdout)
        failure_xml = dump_ui(private)
        fdroid_labels = []
        system_package_seen = False
        if failure_xml is not None:
            try:
                tree = ET.parse(failure_xml).getroot()
                for node in tree.iter("node"):
                    package = node.attrib.get("package", "")
                    if package in ("com.android.settings", "com.google.android.permissioncontroller",
                                   "com.android.permissioncontroller"):
                        system_package_seen = True
                    if package == FDROID_PACKAGE:
                        fdroid_labels.append(
                            (node.attrib.get("text", "") or
                             node.attrib.get("content-desc", "")).strip())
            except (ET.ParseError, OSError):
                pass
        diagnostic = {
            "schema_version": 1, "source_sha": source_sha, "requested_stage": stage,
            "official_app_install_button_actually_tapped": clicked_client_button,
            "system_installer_confirmation_actually_tapped": clicked_system_prompt,
            "actual_native_installed_version_at_failure": installed_version(),
            "fdroid_target_app_name_visible": any(
                label in ("هَماپ", "هماپ", "HamApp") for label in fdroid_labels),
            "fdroid_install_label_visible": "Install" in fdroid_labels,
            "fdroid_update_label_visible": "Update" in fdroid_labels,
            "fdroid_got_it_hint_visible": "Got it" in fdroid_labels,
            "android_permission_or_settings_screen_seen": system_package_seen,
            "install_or_upgrade_verified": False,
            "public_release_authorized": False,
        }
        (output / f"official-inclient-blocker-v{stage}.json").write_text(
            json.dumps(diagnostic, indent=2, sort_keys=True) + "\\n",
            encoding="utf-8")
        print("OFFICIAL_FDROID_REAL_INCLIENT_DIAGNOSTIC_CAPTURED_NO_FAKE_INSTALL")
    raise ClientInstallFailure(
        "official F-Droid in-app install/update did not reach exact native package "
        "version with real APK download and validated Android signer")


def main():
    parser = argparse.ArgumentParser(description="Real in-client official F-Droid install/upgrade")
    parser.add_argument("--stage", type=int, choices=(1, 2), required=True)
    args = parser.parse_args()
    try:
        run(args.stage)
    except (OSError, ValueError, UnicodeError, subprocess.TimeoutExpired) as exc:
        parser.exit(1, "REAL_OFFICIAL_FDROID_INCLIENT_APK_INSTALL_NOT_ACCEPTED: " + str(exc) + "\n")


if __name__ == "__main__":
    main()
