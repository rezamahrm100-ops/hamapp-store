package ir.hamapp.store;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

/** HamApp Android native preview. F-Droid is the installer; no APK sideloading. */
public final class MainActivity extends Activity {
    private final int bg = Color.rgb(11, 18, 32);
    private final int panel = Color.rgb(28, 40, 60);
    private final int white = Color.rgb(245, 248, 252);
    private final int muted = Color.rgb(181, 197, 211);
    private JSONArray apps = new JSONArray();
    private JSONObject repo = null;
    private LinearLayout cards;
    private EditText query;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(bg);
        getWindow().setNavigationBarColor(bg);
        try {
            JSONObject catalog = new JSONObject(loadAsset("android-catalog.json"));
            if (catalog.getInt("schema_version") != 1) throw new JSONException("Unsupported catalog");
            apps = catalog.getJSONArray("apps");
            JSONObject config = new JSONObject(loadAsset("android-repository.json"));
            if (config.getInt("schema_version") != 1) throw new JSONException("Unsupported repository");
            if (!config.isNull("repository")) {
                JSONObject candidate = config.getJSONObject("repository");
                if (!RepoPolicy.isAllowed(candidate.getString("url"), candidate.getString("fingerprint"))) {
                    throw new JSONException("Untrusted repository metadata");
                }
                repo = candidate;
            }
        } catch (IOException | JSONException ex) {
            apps = new JSONArray();
            repo = null;
            showError(ex.getMessage());
        }
        construct();
    }

    private String loadAsset(String file) throws IOException {
        try (InputStream stream = getAssets().open(file);
             ByteArrayOutputStream out = new ByteArrayOutputStream()) {
            byte[] bytes = new byte[4096];
            int n;
            while ((n = stream.read(bytes)) != -1) {
                if (out.size() > 1024 * 1024) throw new IOException("Catalog too large");
                out.write(bytes, 0, n);
            }
            return out.toString(StandardCharsets.UTF_8.name());
        }
    }

    private int dp(int size) {
        return Math.round(getResources().getDisplayMetrics().density * size);
    }

    private TextView text(String value, int size, int color, boolean bold) {
        TextView view = new TextView(this);
        view.setText(value);
        view.setTextSize(size);
        view.setTextColor(color);
        view.setGravity(Gravity.RIGHT);
        view.setTextDirection(View.TEXT_DIRECTION_RTL);
        if (bold) view.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        return view;
    }

    private LinearLayout.LayoutParams margin(int top, int bottom) {
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.topMargin = dp(top);
        lp.bottomMargin = dp(bottom);
        return lp;
    }

    private void construct() {
        LinearLayout main = new LinearLayout(this);
        main.setOrientation(LinearLayout.VERTICAL);
        main.setPadding(dp(18), dp(22), dp(18), dp(15));
        main.setBackgroundColor(bg);
        main.setLayoutDirection(View.LAYOUT_DIRECTION_RTL);

        main.addView(text("هَماپ", 29, white, true), margin(0, 3));
        main.addView(text("فروشگاه برنامه‌ها | نسخهٔ آزمایشی اندروید", 13, muted, false), margin(0, 14));

        query = new EditText(this);
        query.setTextColor(white);
        query.setHintTextColor(muted);
        query.setSingleLine(true);
        query.setTextDirection(View.TEXT_DIRECTION_RTL);
        query.setHint("جست‌وجوی برنامه‌ها");
        query.setContentDescription("جست‌وجوی برنامه‌ها");
        query.setPadding(dp(10), dp(6), dp(10), dp(6));
        main.addView(query, margin(0, 10));

        TextView status = text(repo == null
                ? "مخزن امضاشده هنوز تأیید نشده؛ نصب غیرفعال است."
                : "نصب برنامه‌ها از طریق کلاینت رسمی F-Droid انجام می‌شود.", 12, muted, false);
        main.addView(status, margin(0, 13));

        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        cards = new LinearLayout(this);
        cards.setOrientation(LinearLayout.VERTICAL);
        cards.setLayoutDirection(View.LAYOUT_DIRECTION_RTL);
        scroll.addView(cards);
        main.addView(scroll, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));
        main.addView(text("هیچ بسته‌ای بدون تأیید ناشر و امضای مخزن قابل نصب نیست.", 11, muted, false),
                margin(10, 0));
        setContentView(main);
        query.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) { render(s.toString()); }
            @Override public void afterTextChanged(Editable s) {}
        });
        render("");
    }

    private void render(String search) {
        cards.removeAllViews();
        String filter = search.trim().toLowerCase(java.util.Locale.ROOT);
        for (int i = 0; i < apps.length(); i++) {
            JSONObject app = apps.optJSONObject(i);
            if (app == null) continue;
            String name = app.optString("name_fa", "");
            String description = app.optString("description", "");
            if (!(name + " " + description).toLowerCase(java.util.Locale.ROOT).contains(filter)) continue;
            LinearLayout card = new LinearLayout(this);
            card.setOrientation(LinearLayout.VERTICAL);
            card.setLayoutDirection(View.LAYOUT_DIRECTION_RTL);
            card.setPadding(dp(17), dp(17), dp(17), dp(17));
            card.setBackgroundColor(panel);
            card.addView(text(name, 20, white, true), margin(0, 6));
            card.addView(text(description, 13, muted, false), margin(0, 10));

            boolean approved = app.optString("status").equals("available") && repo != null;
            String state = approved ? "برنامهٔ تأییدشده: " + app.optString("version") : "در دست توسعه";
            card.addView(text(state, 12, approved ? Color.rgb(130, 231, 190) : muted, false),
                    margin(0, 9));
            Button action = new Button(this);
            action.setAllCaps(false);
            action.setText("مدیریت از طریق F-Droid");
            action.setEnabled(approved);
            action.setContentDescription(approved ? "بازکردن مخزن امضاشده در F-Droid"
                    : "نصب هنوز فعال نیست");
            if (approved) action.setOnClickListener(view -> openApprovedRepo());
            card.addView(action, margin(0, 0));
            cards.addView(card, margin(0, 10));
        }
        if (cards.getChildCount() == 0) {
            cards.addView(text("برنامه‌ای پیدا نشد.", 15, muted, false), margin(24, 0));
        }
    }

    private void openApprovedRepo() {
        if (repo == null) return;
        String url = repo.optString("url", "");
        String fingerprint = repo.optString("fingerprint", "");
        if (!RepoPolicy.isAllowed(url, fingerprint)) {
            showError("پیکربندی مخزن نامعتبر است.");
            return;
        }
        new AlertDialog.Builder(this)
            .setTitle("انتقال به F-Droid")
            .setMessage("برای نصب یا به‌روزرسانی از مخزن امضاشده، برنامهٔ F-Droid باید روی گوشی نصب باشد. "
                       + "هَماپ هیچ بسته‌ای را در پس‌زمینه نصب نمی‌کند. ادامه می‌دهید؟")
            .setNegativeButton("لغو", null)
            .setPositiveButton("ادامه", (dialog, which) -> {
                Uri uri = Uri.parse(url).buildUpon().appendQueryParameter("fingerprint", fingerprint).build();
                Intent intent = new Intent(Intent.ACTION_VIEW, uri);
                intent.addCategory(Intent.CATEGORY_BROWSABLE);
                try { startActivity(intent); }
                catch (ActivityNotFoundException ex) { showError("برای ادامه مرورگر یا F-Droid لازم است."); }
            }).show();
    }

    private void showError(String message) {
        new AlertDialog.Builder(this).setTitle("خطای اعتبارسنجی")
                .setMessage(message).setPositiveButton("باشه", null).show();
    }
}
