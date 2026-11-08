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

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;

/**
 * Owner-controlled list of independently pinned personal F-Droid repositories.
 *
 * The official repository and approved HamApp publishers are separate trust
 * domains. Adding a personal repo never authorizes an app in the HamApp public
 * catalogue, and no account token or private signing key is stored here.
 */
public final class UserRepoSettings {
    private static final String PREFS = "personal_fdroid_repo_v1";
    private static final String URL = "repository_url"; // legacy one-repo setting
    private static final String FP = "trusted_index_fingerprint"; // legacy pin
    private static final String LIST = "signed_repositories_v2";
    private static final int MAX_REPOSITORIES = 6;

    public static final class Repository {
        public final String url;
        public final String fingerprint;

        Repository(String url, String fingerprint) {
            if (!RepoPolicy.isAllowed(url, fingerprint))
                throw new IllegalArgumentException("invalid signed repo identity");
            this.url = url;
            this.fingerprint = fingerprint.toLowerCase(Locale.ROOT);
        }

        String label() {
            String host = url.substring("https://".length());
            int slash = host.indexOf('/');
            if (slash >= 0) host = host.substring(0, slash);
            return host + " · " + fingerprint.substring(0, 12) + "…";
        }
    }

    private UserRepoSettings() {}

    private static SharedPreferences storage(Activity activity) {
        return activity.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    /**
     * Corrupt or ambiguous stored trust data fails closed: the store will not
     * use that source until the user explicitly repairs their settings.
     */
    public static List<Repository> saved(Activity activity) {
        SharedPreferences preferences = storage(activity);
        String raw = preferences.getString(LIST, null);
        if (raw == null) {
            String oldUrl = preferences.getString(URL, "");
            String oldPin = preferences.getString(FP, "");
            if (!RepoPolicy.isAllowed(oldUrl, oldPin))
                return Collections.emptyList();
            return Collections.singletonList(new Repository(oldUrl, oldPin));
        }
        try {
            JSONArray array = new JSONArray(raw);
            if (array.length() > MAX_REPOSITORIES)
                throw new IllegalStateException("repository limit exceeded");
            List<Repository> result = new ArrayList<>();
            for (int i = 0; i < array.length(); i++) {
                JSONObject item = array.getJSONObject(i);
                if (item.length() != 2 || !item.has("url") || !item.has("fingerprint"))
                    throw new JSONException("unexpected trusted repo schema");
                Repository repository = new Repository(
                        item.getString("url"), item.getString("fingerprint"));
                for (Repository previous : result) {
                    if (previous.url.equals(repository.url))
                        throw new IllegalStateException("duplicate repository identity");
                }
                result.add(repository);
            }
            return Collections.unmodifiableList(result);
        } catch (JSONException | IllegalArgumentException ex) {
            throw new IllegalStateException("stored repository trust metadata needs repair", ex);
        }
    }

    private static void persist(Activity activity, List<Repository> repositories) {
        if (repositories.size() > MAX_REPOSITORIES)
            throw new IllegalArgumentException("too many repositories");
        JSONArray array = new JSONArray();
        for (Repository repository : repositories) {
            JSONObject item = new JSONObject();
            try {
                item.put("url", repository.url);
                item.put("fingerprint", repository.fingerprint);
            } catch (JSONException ex) {
                throw new IllegalStateException("repository serialization failed", ex);
            }
            array.put(item);
        }
        if (!storage(activity).edit().putString(LIST, array.toString())
                .remove(URL).remove(FP).commit())
            throw new IllegalStateException("repository trust settings were not saved");
    }

    public static boolean configured(Activity activity) {
        try {
            return !saved(activity).isEmpty();
        } catch (IllegalStateException corrupted) {
            return false;
        }
    }

    public static void openSaved(Activity activity, String query) {
        try {
            List<Repository> items = saved(activity);
            if (items.isEmpty()) {
                new AlertDialog.Builder(activity).setTitle("مخزن شخصی تنظیم نشده است")
                        .setMessage("مخزن HTTPS و اثرانگشت امضای آن را به هَماپ اضافه کنید.")
                        .setNegativeButton("بستن", null)
                        .setPositiveButton("افزودن مخزن", (d, w) -> add(activity))
                        .show();
                return;
            }
            String[] labels = new String[items.size()];
            for (int i = 0; i < items.size(); i++) labels[i] = items.get(i).label();
            new AlertDialog.Builder(activity)
                    .setTitle("انتخاب مخزن امضاشده")
                    .setItems(labels, (d, index) -> {
                        Repository selected = items.get(index);
                        InternalFdroidStore.openSubscribed(
                                activity, selected.url, selected.fingerprint, query);
                    })
                    .setNegativeButton("بستن", null)
                    .setPositiveButton("مدیریت مخزن‌ها", (d, w) -> show(activity))
                    .show();
        } catch (IllegalStateException ex) {
            failure(activity, "اطلاعات اعتماد مخزن‌ها مخدوش است؛ از این مخزن‌ها استفاده نشد.");
        }
    }

    public static void show(Activity activity) {
        try {
            List<Repository> items = saved(activity);
            StringBuilder message = new StringBuilder(
                    "هر مخزن کلید امضای مستقل دارد. تعویض اثرانگشت بدون حذف و ثبت دوباره مجاز نیست.\n" +
                    "این مخزن‌ها ناشران تأییدشدهٔ فروشگاه اختصاصی نیستند.\n\n");
            for (int i = 0; i < items.size(); i++) {
                message.append(i + 1).append(". ").append(items.get(i).label()).append("\n");
            }
            if (items.isEmpty()) message.append("هنوز مخزنی ثبت نشده است.");
            new AlertDialog.Builder(activity)
                    .setTitle("مدیریت مخزن‌های امضاشده")
                    .setMessage(message.toString())
                    .setNegativeButton("بستن", null)
                    .setNeutralButton("حذف مخزن", (d, w) -> remove(activity))
                    .setPositiveButton("افزودن مخزن", (d, w) -> add(activity))
                    .show();
        } catch (IllegalStateException ex) {
            failure(activity, "تنظیمات مخزن‌ها قابل خواندن نیست؛ اعتماد جدیدی ثبت نشد.");
        }
    }

    private static void add(Activity activity) {
        LinearLayout form = new LinearLayout(activity);
        form.setOrientation(LinearLayout.VERTICAL);
        form.setLayoutDirection(View.LAYOUT_DIRECTION_RTL);
        int pad = Math.round(activity.getResources().getDisplayMetrics().density * 18);
        form.setPadding(pad, pad / 2, pad, 0);
        TextView instruction = new TextView(activity);
        instruction.setText("فقط نشانی HTTPS مخزن و اثرانگشت SHA-256 را از دو مسیر مستقل بررسی کنید. " +
                "کلید خصوصی امضا یا توکن ورود را در این پنجره وارد نکنید.");
        form.addView(instruction);
        EditText url = new EditText(activity);
        url.setSingleLine(true);
        url.setTextDirection(View.TEXT_DIRECTION_LTR);
        url.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_URI);
        url.setHint("https://example.org/fdroid/repo/");
        form.addView(url);
        EditText pin = new EditText(activity);
        pin.setSingleLine(true);
        pin.setTextDirection(View.TEXT_DIRECTION_LTR);
        pin.setInputType(InputType.TYPE_CLASS_TEXT);
        pin.setHint("SHA-256 (64 hex)");
        form.addView(pin);
        new AlertDialog.Builder(activity)
                .setTitle("افزودن مخزن مستقل")
                .setView(form)
                .setNegativeButton("لغو", null)
                .setPositiveButton("ثبت و بررسی امضا", (d, which) -> {
                    try {
                        String endpoint = url.getText().toString().trim();
                        String fingerprint = pin.getText().toString().replace(":", "")
                                .trim().toLowerCase(Locale.ROOT);
                        Repository candidate = new Repository(endpoint, fingerprint);
                        List<Repository> items = new ArrayList<>(saved(activity));
                        if (items.size() >= MAX_REPOSITORIES)
                            throw new IllegalArgumentException("حداکثر شش مخزن شخصی مجاز است.");
                        for (Repository item : items) {
                            if (item.url.equals(candidate.url))
                                throw new IllegalArgumentException(
                                        "برای تعویض کلید امضای این مخزن، ابتدا مخزن قبلی را حذف کنید.");
                        }
                        items.add(candidate);
                        persist(activity, items);
                        InternalFdroidStore.openSubscribed(
                                activity, candidate.url, candidate.fingerprint, "");
                    } catch (IllegalArgumentException | IllegalStateException ex) {
                        failure(activity, "مخزن ثبت نشد: " + ex.getMessage());
                    }
                }).show();
    }

    private static void remove(Activity activity) {
        try {
            List<Repository> items = saved(activity);
            if (items.isEmpty()) {
                failure(activity, "هیچ مخزن شخصی برای حذف وجود ندارد.");
                return;
            }
            String[] labels = new String[items.size()];
            for (int i = 0; i < items.size(); i++) labels[i] = items.get(i).label();
            new AlertDialog.Builder(activity)
                    .setTitle("حذف مخزن و فهرست ذخیره‌شدهٔ آن")
                    .setItems(labels, (d, which) -> {
                        Repository selected = items.get(which);
                        new AlertDialog.Builder(activity)
                                .setTitle("حذف اعتماد به مخزن؟")
                                .setMessage("اتصال، اثرانگشت و نسخهٔ آفلاین این مخزن حذف می‌شود. " +
                                        "برنامه‌های نصب‌شدهٔ دستگاه حذف نخواهند شد.")
                                .setNegativeButton("لغو", null)
                                .setPositiveButton("تأیید حذف", (confirm, button) -> {
                                    try {
                                        List<Repository> remaining = new ArrayList<>(saved(activity));
                                        remaining.removeIf(r -> r.url.equals(selected.url) &&
                                                r.fingerprint.equals(selected.fingerprint));
                                        persist(activity, remaining);
                                        InternalFdroidStore.dropCache(
                                                activity, selected.url, selected.fingerprint);
                                        show(activity);
                                    } catch (IllegalStateException ex) {
                                        failure(activity, "حذف مخزن به‌طور کامل ثبت نشد.");
                                    }
                                }).show();
                    })
                    .setNegativeButton("بستن", null).show();
        } catch (IllegalStateException ex) {
            failure(activity, "مخزن‌های ذخیره‌شده معتبر نیستند.");
        }
    }

    private static void failure(Activity activity, String message) {
        new AlertDialog.Builder(activity).setTitle("تنظیم مخزن انجام نشد")
                .setMessage(message).setPositiveButton("بستن", null).show();
    }
}
