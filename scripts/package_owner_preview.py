#!/usr/bin/env python3
"""Package honest owner-installable HamApp test previews from GitHub-hosted builds.

A review-only delivery manifest: no production signature, approved publisher,
public catalogue download link, or successful installation is implied.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import zipfile

SOURCE_SHA = re.compile(r"^[0-9a-f]{40}$")
PRODUCTS = {
    "android": ("HamApp-Android-Preview-debug.apk",),
    "windows": ("HamApp-Windows-Preview.exe",
                "HamApp-Preview-Setup-UNSIGNED.exe"),
}
NOTES = {
    "android": (
        "# هَماپ | نسخهٔ آزمایشی اندروید\n\n"
        "فایل: `HamApp-Android-Preview-debug.apk`\n\n"
        "این APK با کلید موقت Debug ساخته شده است، امضای انتشار رسمی ندارد "
        "و فقط برای نصب و آزمایش شخصی ارائه می‌شود. با اجازهٔ خودتان فایل را "
        "روی دستگاه اندروید باز کنید و هش SHA-256 آن را با SHA256SUMS.txt بسنجید.\n\n"
        "اگر قبلاً نسخه‌ای با گواهی متفاوت نصب کرده‌اید، اندروید ممکن است "
        "به‌روزرسانی را رد کند؛ حذف نسخهٔ قبلی می‌تواند داده‌هایش را پاک کند. "
        "از اطلاعات مهم نسخهٔ پشتیبان بگیرید.\n\n"
        "در بخش کاوش F-Droid می‌توانید فروشگاه عمومی مستقل را با رضایت خود باز کنید. فهرست اختصاصی هَماپ تا تأیید ناشر غیرفعال است.\n"
    ),
    "windows": (
        "# هَماپ | نسخهٔ آزمایشی ویندوز\n\n"
        "برای نصب انتخابی و قابل‌حذف از `HamApp-Preview-Setup-UNSIGNED.exe` "
        "استفاده کنید. برای اجرای مستقل بدون نصب، فایل "
        "`HamApp-Windows-Preview.exe` در دسترس است.\n\n"
        "هردو فایل **فاقد امضای معتبر ناشر** هستند و تنها برای آزمایش شخصی "
        "ارائه می‌شوند. قبل از اجرا SHA-256 را با SHA256SUMS.txt مقایسه کنید؛ "
        "در صورت هشدار امنیتی ویندوز بدون اطمینان از منشأ فایل آن را اجرا نکنید.\n\n"
        "نصب‌کننده فقط در محدودهٔ حساب کاربر نصب می‌کند؛ حذف آن از "
        "Settings > Apps یا Uninstall.exe ممکن است. "
        "بخش مستقل کاوش WinGet امکان جستجو و نصب/ارتقای بسته‌های ثالث را با رضایت کاربر دارد. "
        "ناشر این بسته‌ها توسط هَماپ تأیید نشده؛ فهرست اختصاصی هنوز تنها برای بسته‌های تأییدشده فعال می‌شود.\n"
    ),
}


class DeliveryError(ValueError):
    """A source artifact is not suitable for owner test delivery."""


def inspect(directory: Path, platform: str, sha: str):
    if platform not in PRODUCTS or not SOURCE_SHA.fullmatch(sha):
        raise DeliveryError("invalid delivery platform/source commit")
    if not directory.is_dir() or directory.is_symlink():
        raise DeliveryError("delivery directory must be a real directory")
    rows = []
    for name in PRODUCTS[platform]:
        path = directory / name
        if not path.is_file() or path.is_symlink() or path.stat().st_size < 1024:
            raise DeliveryError("missing, linked or implausibly small build: " + name)
        with path.open("rb") as fh:
            magic = fh.read(4)
        if platform == "android":
            if magic[:2] != b"PK" or not zipfile.is_zipfile(path):
                raise DeliveryError("Android debug APK is not a valid ZIP container")
            with zipfile.ZipFile(path) as archive:
                if archive.testzip() is not None or "AndroidManifest.xml" not in archive.namelist():
                    raise DeliveryError("APK archive integrity/manifest missing")
        elif magic[:2] != b"MZ":
            raise DeliveryError("Windows build lacks PE signature")
        digest = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                digest.update(chunk)
        rows.append({"filename": name, "bytes": path.stat().st_size,
                     "sha256": digest.hexdigest()})
    return {
        "schema_version": 1,
        "source_commit": sha,
        "platform": platform,
        "scope": "owner-local-debug-or-unsigned-preview-only",
        "build_files": rows,
        "production_signed": False,
        "public_release_authorized": False,
        "owner_device_tested": False,
        "third_party_downloads_enabled": False,
    }


def write_delivery(directory: Path, platform: str, sha: str):
    manifest = inspect(directory, platform, sha)
    for filename in ("manifest.json", "SHA256SUMS.txt", "README_FA.md"):
        target = directory / filename
        if target.exists() or target.is_symlink():
            raise DeliveryError("refusing to overwrite existing delivery metadata")
    (directory / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8")
    (directory / "SHA256SUMS.txt").write_text(
        "".join(row["sha256"] + "  " + row["filename"] + "\n"
                for row in manifest["build_files"]), encoding="utf-8")
    (directory / "README_FA.md").write_text(
        NOTES[platform] + "\nکد منبع GitHub: `" + sha + "`\n",
        encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices=tuple(PRODUCTS), required=True)
    parser.add_argument("--directory", type=Path, required=True)
    options = parser.parse_args()
    if os.environ.get("GITHUB_ACTIONS") != "true" or os.environ.get(
            "GITHUB_REPOSITORY") != "rezamahrm100-ops/hamapp-store":
        raise SystemExit("test preview delivery restricted to repository GitHub Actions")
    sha = os.environ.get("GITHUB_SHA", "")
    try:
        manifest = write_delivery(options.directory, options.platform, sha)
    except (DeliveryError, OSError, zipfile.BadZipFile) as exc:
        raise SystemExit("PREVIEW_DELIVERY_REJECTED: " + str(exc)) from exc
    print("HAMAPP_OWNER_PREVIEW_PACKAGED_" + manifest["platform"].upper()
          + "_TEST_ONLY_" + sha)


if __name__ == "__main__":
    main()
