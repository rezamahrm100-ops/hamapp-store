package ir.hamapp.store;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.SharedPreferences;
import android.text.InputType;
import android.view.View;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.util.Locale;

/**
 * Optional user-supplied signed F-Droid subscription.
 * This is a personal source, NOT an approved HamApp publisher identity.
 * No private signing keys or access tokens are collected.
 */
public final class UserRepoSettings {
    private static final String PREFS = "personal_fdroid_repo_v1";
    private static final String URL = "repository_url";
    private static final String FP = "trusted_index_fingerprint";

    private UserRepoSettings() {}

    private static SharedPreferences storage(Activity activity) {
        return activity.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    public static boolean configured(Activity activity) {
        SharedPreferences prefs = storage(activity);
        return RepoPolicy.isAllowed(prefs.getString(URL, ""), prefs.getString(FP, ""));
    }

    public static void openSaved(Activity activity, String query) {
        SharedPreferences prefs = storage(activity);
        String url = prefs.getString(URL, "");
        String fingerprint = prefs.getString(FP, "");
        if (!RepoPolicy.isAllowed(url, fingerprint)) {
            new AlertDialog.Builder(activity)
                    .setTitle("مخزن شخصی تنظیم نشده است")
                    .setMessage("نشانی HTTPS مخزن و اثرانگشت SHA-256 آن را در تنظیمات ثبت کنید.")
                    .setNegativeButton("بستن", null)
                    .setPositiveButton("تنظیمات", (dialog, button) -> show(activity))
                    .show();
            return;
        }
        InternalFdroidStore.openSubscribed(activity, url, fingerprint, query);
    }

    public static void show(Activity activity) {
        SharedPreferences prefs = storage(activity);
        LinearLayout box = new LinearLayout(activity);
        box.setOrientation(LinearLayout.VERTICAL);
        int pad = Math.round(activity.getResources().getDisplayMetrics().density * 18);
        box.setPadding(pad, pad / 2, pad, 0);
        box.setLayoutDirection(View.LAYOUT_DIRECTION_RTL);

        TextView help = new TextView(activity);
        help.setText("فقط نشانی مخزن F-Droid امضاشده و اثرانگشت SHA-256 " +
                "را وارد کنید. اثرانگشت را مستقل از خود وب‌سایت مخزن بررسی کنید؛ " +
                "اعتماد به مخزن شخصی به معنای تأیید ناشر توسط هَماپ نیست. " +
                "کلید خصوصی امضا را هرگز اینجا وارد نکنید.");
        box.addView(help);

        TextView urlTitle = new TextView(activity);
        urlTitle.setText("نشانی مخزن HTTPS");
        box.addView(urlTitle);
        EditText url = new EditText(activity);
        url.setSingleLine(true);
        url.setTextDirection(View.TEXT_DIRECTION_LTR);
        url.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_URI);
        url.setHint("https://example.org/fdroid/repo/");
        url.setText(prefs.getString(URL, ""));
        box.addView(url);

        TextView fpTitle = new TextView(activity);
        fpTitle.setText("اثر انگشت امضای مخزن، ۶۴ نویسهٔ هگزادسیمال");
        box.addView(fpTitle);
        EditText fingerprint = new EditText(activity);
        fingerprint.setSingleLine(true);
        fingerprint.setTextDirection(View.TEXT_DIRECTION_LTR);
        fingerprint.setHint("SHA-256");
        fingerprint.setText(prefs.getString(FP, ""));
        box.addView(fingerprint);

        new AlertDialog.Builder(activity)
                .setTitle("تنظیم مخزن شخصی در هَماپ")
                .setView(box)
                .setNegativeButton("لغو", null)
                .setNeutralButton("حذف اتصال", (dialog, which) -> {
                    prefs.edit().remove(URL).remove(FP).apply();
                    new AlertDialog.Builder(activity).setMessage("اتصال مخزن شخصی حذف شد.")
                            .setPositiveButton("باشه", null).show();
                })
                .setPositiveButton("ذخیره و بررسی امضا", (dialog, which) -> {
                    String endpoint = url.getText().toString().trim();
                    String pin = fingerprint.getText().toString()
                            .replace(":", "").trim().toLowerCase(Locale.ROOT);
                    if (!RepoPolicy.isAllowed(endpoint, pin)) {
                        new AlertDialog.Builder(activity).setTitle("اطلاعات نامعتبر")
                                .setMessage("نشانی باید دقیقاً HTTPS با مسیر /fdroid/repo/ و " +
                                        "اثر انگشت باید ۶۴ نویسهٔ هگزادسیمال باشد.")
                                .setNegativeButton("بستن", null)
                                .setPositiveButton("اصلاح", (d, w) -> show(activity)).show();
                        return;
                    }
                    prefs.edit().putString(URL, endpoint).putString(FP, pin).apply();
                    // Actual repository authenticity is verified against this
                    // independently provided fingerprint before displaying apps.
                    openSaved(activity, "");
                }).show();
    }
}
