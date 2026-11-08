## محیط اختیاری بازبینی و امضای ناشر

این مخزن دو سرویس با مسئولیت جداگانه دارد:

- `publisher-intake`: سرویس پیش‌فرض TLS روی `localhost:8766`؛ دریافت و قرنطینهٔ خصوصی. هیچ کلید امضا، اسکن AV، تأیید ناشر یا انتشار ندارد.
- `owner-review`: یک **پروفایل اختیاری** Docker Compose؛ به‌صورت خودکار بالا نمی‌آید، هیچ پورتی باز نمی‌کند و فقط هنگام اجرای صریح، با داده‌های قرنطینهٔ همان سامانه، ابزارهای رسمی `fdroidserver`، `apksigner`، `aapt`، `gh attestation verify` و `ClamAV` را اجرا می‌کند.

پروفایل خصوصی احراز هویت GitHub CLI نیز به‌صورت پایدار فقط در مسیر `/owner/gh` و در همان پوشهٔ خصوصی مالک قرار می‌گیرد؛ هیچ توکن GitHub در `compose.yaml`، آرگومان فرمان یا بستهٔ انتشار قرار نمی‌گیرد. اتصال حساب و مجوزهای واقعی مالک هنوز نیازمند اقدام آگاهانهٔ خود اوست.

تصویر دوم دارای ابزارهای نصب‌شده است ولی فاقد کلید تولیدی، حساب واقعی و فهرست آنتی‌ویروس ثابتِ قابل اعتماد است. پیش از هر بازبینی، `freshclam` پایگاه امضا را در پوشهٔ خصوصی مالک به‌روز می‌کند و در صورت شکست، فرایند متوقف می‌شود. بستهٔ APK هرگز مستقیم به فروشگاه عمومی یا GitHub Upload ارسال نمی‌شود.

برای آماده‌سازی محیط شخصی هنگام راه‌اندازی آینده، یک پوشهٔ خصوصی مجزا در سیستم میزبان معرفی کنید؛ Docker آن را **ایجاد خودکار نمی‌کند** و نباید آن را به‌عنوان Git checkout عمومی به کار برد. متغیر محیطی `HAMAPP_OWNER_REVIEW_DIR` باید به همان پوشه اشاره کند. اطلاعات هویتی، گواهی و کلید خصوصی فقط در همین محیط مالک باقی می‌مانند.

نمونهٔ درخواست (بعد از آماده‌کردن هویت‌های واقعی، بازبینی مستقل و مجوزهای لازم):

```bash
HAMAPP_OWNER_REVIEW_DIR=/secure/hamapp-owner-review \
  docker compose -f deployment/compose.yaml -p hamapp-private \
  --profile owner-review run --rm --no-deps owner-review \
    --private-inbox-root /data/service/inbox \
    --submission-id ACTUAL_32_HEX_ID \
    --fdroid-workspace /owner/signer-workspace \
    --registry /owner/trusted_signers.json \
    --history /owner/release_history.json \
    --android-permissions-policy /owner/permissions.json \
    --trusted-workflow rezamahrm100-ops/APP/.github/workflows/release.yml \
    --trusted-source-ref refs/tags/v1.2.3 \
    --expected-repo-fingerprint 64_HEX_FROM_AN_INDEPENDENT_SOURCE \
    --output-dir /owner/reviews/new-private-review
```

برنامهٔ بررسی درون همین تصویر و با شناسهٔ کاربری غیرریشهٔ `10001` اجرا می‌شود. پوشهٔ میزبان باید مجوزهای مناسب و دسترسی همان کاربر را داشته باشد. در صورت نبود کلیدها یا ناهماهنگی مالکیت/امضای بسته، خروجی **رد** می‌شود؛ مجوزها نباید با `chmod 777` دور زده شوند.

صحت تصویر، نسخهٔ ابزارها و جدا ماندن سرویس بازبینی از سرویس پیش‌فرض باید با CI روی رانر میزبانی‌شدهٔ GitHub اثبات شود. ساخت موفق Docker به معنی تأیید ناشر یا عملیاتی‌شدن امضای تولیدی نیست.
