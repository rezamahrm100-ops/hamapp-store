package ir.hamapp.store;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.net.Uri;
import android.view.ViewGroup;
import android.widget.ProgressBar;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;
import org.json.JSONTokener;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.regex.Pattern;

/**
 * Read-only public F-Droid discovery inside HamApp.
 *
 * Upstream search is display-only and is NOT cryptographic release metadata.
 * Installation remains entirely in the official separately installed F-Droid
 * companion. Neither this client nor this API authorizes package installation.
 */
public final class PublicFdroidSearch {
    private static final String SEARCH = "https://search.f-droid.org/api/search_apps";
    private static final String OFFICIAL_DETAIL = "https://f-droid.org/packages/";
    private static final int MAX_REPLY_BYTES = 1024 * 1024;
    private static final int MAX_RESULTS = 25;
    private static final Pattern PACKAGE_ID =
            Pattern.compile("[A-Za-z][A-Za-z0-9_]*(?:\\.[A-Za-z0-9_]+)+");

    private PublicFdroidSearch() {}

    static final class Result {
        final String id;
        final String title;
        Result(String id, String title) {
            this.id = id;
            this.title = title;
        }
    }

    static String safeQuery(String raw) {
        if (raw == null) throw new IllegalArgumentException("empty search");
        String query = raw.trim();
        if (query.length() < 2 || query.length() > 80) {
            throw new IllegalArgumentException("search length must be 2..80");
        }
        for (int i = 0; i < query.length(); i++) {
            if (Character.isISOControl(query.charAt(i))) {
                throw new IllegalArgumentException("control character in search");
            }
        }
        return query;
    }

    private static String endpoint(String query) {
        return Uri.parse(SEARCH).buildUpon().appendQueryParameter("q", query).build().toString();
    }

    private static String request(String query) throws IOException {
        URL url = new URL(endpoint(query));
        if (!"https".equals(url.getProtocol()) || !"search.f-droid.org".equals(url.getHost())) {
            throw new IOException("unapproved search origin");
        }
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setInstanceFollowRedirects(false);
        connection.setRequestMethod("GET");
        connection.setConnectTimeout(7000);
        connection.setReadTimeout(7000);
        connection.setRequestProperty("Accept", "application/json");
        try {
            if (connection.getResponseCode() != HttpURLConnection.HTTP_OK) {
                throw new IOException("search unavailable");
            }
            try (InputStream stream = connection.getInputStream();
                    ByteArrayOutputStream bytes = new ByteArrayOutputStream()) {
                byte[] buffer = new byte[8192];
                int total = 0;
                int count;
                while ((count = stream.read(buffer)) != -1) {
                    total += count;
                    if (total > MAX_REPLY_BYTES) throw new IOException("search reply too large");
                    bytes.write(buffer, 0, count);
                }
                return bytes.toString(StandardCharsets.UTF_8.name());
            }
        } finally {
            connection.disconnect();
        }
    }

    private static JSONArray findArray(Object raw) {
        if (raw instanceof JSONArray) return (JSONArray) raw;
        if (!(raw instanceof JSONObject)) return null;
        JSONObject object = (JSONObject) raw;
        for (String key : new String[]{"apps", "results", "packages", "items"}) {
            JSONArray list = object.optJSONArray(key);
            if (list != null) return list;
            JSONObject nested = object.optJSONObject(key);
            if (nested != null) {
                JSONArray fromNested = findArray(nested);
                if (fromNested != null) return fromNested;
            }
        }
        return null;
    }

    static List<Result> parse(String json) throws JSONException {
        Object data = new JSONTokener(json).nextValue();
        JSONArray rows = findArray(data);
        if (rows == null) throw new JSONException("unknown search result format");
        List<Result> found = new ArrayList<>();
        for (int i = 0; i < rows.length() && found.size() < MAX_RESULTS; i++) {
            JSONObject item = rows.optJSONObject(i);
            if (item == null) continue;
            String id = "";
            for (String key : new String[]{"packageName", "package_name", "packageId",
                    "applicationId", "package_id", "package", "id"}) {
                String candidate = item.optString(key, "");
                if (PACKAGE_ID.matcher(candidate).matches()) {
                    id = candidate;
                    break;
                }
            }
            if (id.isEmpty()) continue;
            String title = item.optString("name", "");
            if (title.isEmpty()) title = item.optString("title", "");
            if (title.isEmpty()) title = id;
            title = title.replace('\n', ' ').replace('\r', ' ').trim();
            if (title.length() > 70) title = title.substring(0, 70);
            found.add(new Result(id, title));
        }
        return found;
    }

    private static void openOfficialDetail(Activity activity, String id) {
        if (!PACKAGE_ID.matcher(id).matches()) return;
        Uri target = Uri.parse(OFFICIAL_DETAIL + id + "/");
        new AlertDialog.Builder(activity)
                .setTitle("نمایش در F-Droid")
                .setMessage("این نتیجه متعلق به فهرست عمومی F-Droid است، نه ناشران تأییدشدهٔ هَماپ. نصب احتمالی فقط در کلاینت رسمی و با اجازهٔ شما انجام می‌شود.")
                .setNegativeButton("لغو", null)
                .setPositiveButton("ادامه", (dialog, which) -> {
                    Intent intent = new Intent(Intent.ACTION_VIEW, target);
                    intent.addCategory(Intent.CATEGORY_BROWSABLE);
                    intent.setPackage("org.fdroid.fdroid");
                    try {
                        activity.startActivity(intent);
                    } catch (ActivityNotFoundException | SecurityException ex) {
                        try {
                            Intent browser = new Intent(Intent.ACTION_VIEW, target);
                            browser.addCategory(Intent.CATEGORY_BROWSABLE);
                            activity.startActivity(browser);
                        } catch (ActivityNotFoundException | SecurityException ignored) {
                            new AlertDialog.Builder(activity).setTitle("پیوند در دسترس نیست")
                                    .setMessage("کلاینت F-Droid یا مرورگر نصب نشده است.")
                                    .setPositiveButton("باشه", null).show();
                        }
                    }
                }).show();
    }

    private static void openWebSearch(Activity activity, String query) {
        Uri target = Uri.parse("https://search.f-droid.org/")
                .buildUpon().appendQueryParameter("q", query).build();
        try {
            Intent intent = new Intent(Intent.ACTION_VIEW, target);
            intent.addCategory(Intent.CATEGORY_BROWSABLE);
            activity.startActivity(intent);
        } catch (ActivityNotFoundException | SecurityException ex) {
            new AlertDialog.Builder(activity).setTitle("مرورگر در دسترس نیست")
                    .setPositiveButton("باشه", null).show();
        }
    }

    public static void request(Activity activity, String raw) {
        final String query;
        try {
            query = safeQuery(raw);
        } catch (IllegalArgumentException ex) {
            new AlertDialog.Builder(activity).setTitle("عبارت جست‌وجو")
                    .setMessage("ابتدا یک عبارت ۲ تا ۸۰ نویسه‌ای در کادر جست‌وجو بنویسید.")
                    .setPositiveButton("باشه", null).show();
            return;
        }
        new AlertDialog.Builder(activity)
                .setTitle("جست‌وجوی عمومی F-Droid")
                .setMessage("این جست‌وجو عبارت شما را به سرور عمومی F-Droid می‌فرستد. نتیجه فقط برای نمایش است؛ امضای بسته یا ناشر را تأیید نمی‌کند.")
                .setNegativeButton("لغو", null)
                .setPositiveButton("جست‌وجو", (consent, which) -> search(activity, query))
                .show();
    }

    private static void search(Activity activity, String query) {
        ProgressBar spinner = new ProgressBar(activity);
        spinner.setPadding(32, 24, 32, 24);
        AlertDialog progress = new AlertDialog.Builder(activity)
                .setTitle("جست‌وجوی F-Droid")
                .setView(spinner)
                .setCancelable(false)
                .create();
        progress.show();
        new Thread(() -> {
            List<Result> results = null;
            String error = null;
            try {
                results = parse(request(query));
            } catch (IOException | JSONException | IllegalArgumentException ex) {
                error = "پاسخ جست‌وجوی F-Droid دریافت یا تفسیر نشد.";
            }
            final List<Result> completed = results;
            final String failure = error;
            activity.runOnUiThread(() -> {
                if (activity.isFinishing() || activity.isDestroyed()) {
                    progress.dismiss();
                    return;
                }
                progress.dismiss();
                if (failure != null || completed == null || completed.isEmpty()) {
                    new AlertDialog.Builder(activity)
                            .setTitle(failure == null ? "نتیجه‌ای یافت نشد" : "جست‌وجوی درون‌برنامه‌ای ناموفق بود")
                            .setMessage(failure == null ? "برای این عبارت نتیجهٔ قابل نمایش پیدا نشد." : failure)
                            .setNegativeButton("بستن", null)
                            .setPositiveButton("جست‌وجو در وب رسمی", (d, w) -> openWebSearch(activity, query))
                            .show();
                    return;
                }
                String[] labels = new String[completed.size()];
                for (int i = 0; i < completed.size(); i++) {
                    Result item = completed.get(i);
                    labels[i] = item.title + "\n" + item.id;
                }
                new AlertDialog.Builder(activity)
                        .setTitle("نتایج عمومی F-Droid — بدون تأیید ناشر هَماپ")
                        .setItems(labels, (d, position) -> openOfficialDetail(activity, completed.get(position).id))
                        .setNegativeButton("بستن", null)
                        .setNeutralButton("جست‌وجو در وب رسمی", (d, w) -> openWebSearch(activity, query))
                        .show();
            });
        }, "hamapp-fdroid-public-search").start();
    }
}
