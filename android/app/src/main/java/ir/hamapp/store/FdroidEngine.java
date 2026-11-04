package ir.hamapp.store;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.net.Uri;
import org.json.JSONObject;
import java.util.Locale;

/** UI-independent bridge to the official installed F-Droid client.
 * The caller must additionally obtain repo from the build-reviewed asset.
 * This class never downloads APKs, requests install permission or side-loads.
 */
public final class FdroidEngine {
    private FdroidEngine() {}

    public static Uri signedRepositoryUri(String url, String fingerprint) {
        if (!RepoPolicy.isAllowed(url, fingerprint)) {
            throw new IllegalArgumentException("unapproved F-Droid repository metadata");
        }
        Uri source = Uri.parse(url);
        Uri target = source.buildUpon().scheme("fdroidrepos")
                .appendQueryParameter("fingerprint", fingerprint.toUpperCase(Locale.ROOT))
                .build();
        if (!"fdroidrepos".equals(target.getScheme())
                || !source.getHost().equals(target.getHost())
                || !"/fdroid/repo/".equals(target.getPath())) {
            throw new IllegalArgumentException("invalid F-Droid handoff URI");
        }
        return target;
    }

    /** Open the separately installed official F-Droid catalogue, not an
     * owner-approved HamApp repository. No package is downloaded or installed
     * by HamApp itself. Android 11+ package visibility is explicitly scoped.
     */
    public static void requestPublicCatalog(Activity activity) {
        new AlertDialog.Builder(activity)
                .setTitle("کاوش فروشگاه متن‌باز F-Droid")
                .setMessage("فهرست عمومی F-Droid مستقل از ناشران تأییدشدهٔ هَماپ است. "
                        + "نصب و به‌روزرسانی فقط در برنامهٔ رسمی F-Droid و با اجازهٔ اندروید انجام می‌شود. "
                        + "اگر F-Droid نصب نباشد، وب‌سایت رسمی آن باز می‌شود. ادامه می‌دهید؟")
                .setNegativeButton("لغو", null)
                .setPositiveButton("باز کردن", (dialog, which) -> {
                    try {
                        Intent launch = activity.getPackageManager()
                                .getLaunchIntentForPackage("org.fdroid.fdroid");
                        if (launch != null) {
                            activity.startActivity(launch);
                            return;
                        }
                        Intent web = new Intent(Intent.ACTION_VIEW,
                                Uri.parse("https://f-droid.org/"));
                        web.addCategory(Intent.CATEGORY_BROWSABLE);
                        activity.startActivity(web);
                    } catch (ActivityNotFoundException | SecurityException ex) {
                        new AlertDialog.Builder(activity)
                                .setTitle("عدم دسترسی به F-Droid")
                                .setMessage("کلاینت رسمی یا مرورگر قابل اجرا نیست.")
                                .setPositiveButton("باشه", null).show();
                    }
                }).show();
    }

    /** Always shows an explicit approval prompt before leaving HamApp. */
    public static void requestOpen(Activity activity, JSONObject reviewedRepository) {
        if (reviewedRepository == null) return;
        final Uri target;
        try {
            target = signedRepositoryUri(
                    reviewedRepository.getString("url"),
                    reviewedRepository.getString("fingerprint"));
        } catch (Exception ex) {
            new AlertDialog.Builder(activity).setTitle("خطای اعتبارسنجی")
                    .setMessage("پیکربندی مخزن نامعتبر است.")
                    .setPositiveButton("باشه", null).show();
            return;
        }
        new AlertDialog.Builder(activity)
                .setTitle("انتقال به F-Droid")
                .setMessage("برای نصب یا به‌روزرسانی از مخزن امضاشده، برنامهٔ F-Droid باید روی گوشی نصب باشد. "
                        + "هَماپ هیچ بسته‌ای را در پس‌زمینه نصب نمی‌کند. ادامه می‌دهید؟")
                .setNegativeButton("لغو", null)
                .setPositiveButton("ادامه", (dialog, which) -> {
                    Intent intent = new Intent(Intent.ACTION_VIEW, target);
                    intent.addCategory(Intent.CATEGORY_BROWSABLE);
                    intent.setPackage("org.fdroid.fdroid");
                    try {
                        activity.startActivity(intent);
                    } catch (ActivityNotFoundException ex) {
                        new AlertDialog.Builder(activity).setTitle("خطای اعتبارسنجی")
                                .setMessage("کلاینت رسمی F-Droid نصب نیست یا پیوند مخزن را نمی‌پذیرد.")
                                .setPositiveButton("باشه", null).show();
                    }
                }).show();
    }
}
