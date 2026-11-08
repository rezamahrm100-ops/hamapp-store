package ir.hamapp.store;

import android.app.Activity;
import android.app.AlertDialog;
import android.graphics.Color;
import android.content.res.ColorStateList;
import android.graphics.drawable.GradientDrawable;
import android.graphics.Typeface;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import com.google.android.material.button.MaterialButton;
import com.google.android.material.textfield.TextInputLayout;
import com.google.android.material.textfield.TextInputEditText;
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

/** HamApp native store: signed F-Droid index and OS-confirmed embedded installation. */
public final class MainActivity extends Activity {
    private final int bg = Color.rgb(11, 18, 32);
    private final int accent = Color.rgb(159, 227, 199);
    private final int panel = Color.rgb(27, 41, 61);
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

    private GradientDrawable roundedSurface(int color, int radius, int outline) {
        GradientDrawable shape = new GradientDrawable();
        shape.setColor(color);
        shape.setCornerRadius(dp(radius));
        shape.setStroke(dp(1), outline);
        return shape;
    }

    private MaterialButton actionButton(String label, boolean primary) {
        MaterialButton button = new MaterialButton(this);
        button.setAllCaps(false);
        button.setText(label);
        button.setCornerRadius(dp(16));
        button.setMinHeight(dp(50));
        button.setBackgroundTintList(ColorStateList.valueOf(primary ? accent : panel));
        button.setTextColor(primary ? bg : white);
        return button;
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
        main.addView(text("فروشگاه برنامه‌ها | نسخهٔ آزمایشی اندروید", 13, muted, false), margin(0, 7));
        // A usable, separately governed upstream catalogue even when the
        // private HamApp publisher registry has no verified releases yet.
        TextView upstreamLabel = text(
                "فهرست امضاشدهٔ F-Droid داخل هَماپ | مستقل از ناشران اختصاصی",
                12, muted, false);
        main.addView(upstreamLabel, margin(0, 7));
        MaterialButton explore = actionButton("فروشگاه عمومی داخل هَماپ", true);
        explore.setContentDescription(
                "فهرست امضاشده و نصب با تأیید اندروید، در خود هَماپ");
        explore.setOnClickListener(view -> InternalFdroidStore.openPublic(this, ""));
        main.addView(explore, margin(0, 14));
        // Signed index and native OS installer remain inside the HamApp process.
        MaterialButton searchPublic = actionButton("جست‌وجوی عمومی در F-Droid", false);
        searchPublic.setContentDescription("جست‌وجو و نصب برنامه‌های عمومی درون هَماپ");
        searchPublic.setOnClickListener(view ->
                InternalFdroidStore.openPublic(this, query == null ? "" : query.getText().toString()));
        main.addView(searchPublic, margin(0, 13));

        MaterialButton personalRepo = actionButton("افزودن یا تغییر مخزن شخصی", false);
        personalRepo.setContentDescription("تنظیم نشانی HTTPS و اثر انگشت SHA-256 مخزن شخصی، بدون تغییر کد");
        personalRepo.setOnClickListener(view -> UserRepoSettings.show(this));
        main.addView(personalRepo, margin(0, 6));
        MaterialButton openPersonal = actionButton("کاوش مخزن شخصی در هَماپ", false);
        openPersonal.setOnClickListener(view -> UserRepoSettings.openSaved(this, ""));
        main.addView(openPersonal, margin(0, 13));


        query = new TextInputEditText(this);
        query.setTextColor(white);
        query.setHintTextColor(muted);
        query.setSingleLine(true);
        query.setTextDirection(View.TEXT_DIRECTION_RTL);
        query.setHint("جست‌وجوی برنامه‌ها");
        query.setContentDescription("جست‌وجوی برنامه‌ها");
        query.setPadding(dp(10), dp(6), dp(10), dp(6));
        TextInputLayout searchField = new TextInputLayout(this);
        searchField.setHint("جست‌وجوی برنامه‌ها");
        searchField.addView(query);
        main.addView(searchField, margin(0, 10));

        TextView status = text(repo == null
                ? "مخزن اختصاصی هنوز تأیید نشده؛ بخش عمومی مستقل در دسترس است."
                : "مدیریت برنامه‌های اختصاصی از مخزن امضاشده، درون هَماپ است.", 12, muted, false);
        main.addView(status, margin(0, 13));

        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        cards = new LinearLayout(this);
        cards.setOrientation(LinearLayout.VERTICAL);
        cards.setLayoutDirection(View.LAYOUT_DIRECTION_RTL);
        scroll.addView(cards);
        main.addView(scroll, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));
        main.addView(text("هر نصب نیازمند امضای معتبر مخزن و بسته و تأیید اندروید است.", 11, muted, false),
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
            card.setBackground(roundedSurface(panel, 20, Color.rgb(59, 77, 98)));
            card.addView(text(name, 20, white, true), margin(0, 6));
            card.addView(text(description, 13, muted, false), margin(0, 10));

            boolean approved = app.optString("status").equals("available") && repo != null;
            String state = approved ? "برنامهٔ تأییدشده: " + app.optString("version") : "در دست توسعه";
            card.addView(text(state, 12, approved ? Color.rgb(130, 231, 190) : muted, false),
                    margin(0, 9));
            MaterialButton action = actionButton("مدیریت در هَماپ", approved);
            action.setEnabled(approved);
            action.setContentDescription(approved ? "مدیریت مخزن امضاشده در خود هَماپ"
                    : "نصب هنوز فعال نیست");
            if (approved) action.setOnClickListener(view -> openApprovedRepo());
            card.addView(action, margin(0, 4));
            MaterialButton info = actionButton("جزئیات برنامه", false);
            info.setContentDescription("نمایش جزئیات " + name);
            info.setOnClickListener(view -> new AlertDialog.Builder(this)
                    .setTitle(name)
                    .setMessage(description + "\\n\\n"
                            + (approved ? "نسخهٔ ثبت‌شده: " + app.optString("version")
                                    + "\\nمدیریت نصب: موتور داخلی هَماپ"
                                    : "وضعیت: در دست توسعه؛ فایل قابل نصب تأیید نشده است.")
                            + "\\n\\nفروشگاه عمومی متن‌باز از ناشران اختصاصی جداست.")
                    .setPositiveButton("بستن", null).show());
            card.addView(info, margin(0, 0));
            cards.addView(card, margin(0, 10));
        }
        if (cards.getChildCount() == 0) {
            cards.addView(text("برنامه‌ای پیدا نشد.", 15, muted, false), margin(24, 0));
        }
    }

    private void openApprovedRepo() {
        InternalFdroidStore.openApproved(this, repo);
    }

    private void showError(String message) {
        new AlertDialog.Builder(this).setTitle("خطای اعتبارسنجی")
                .setMessage(message).setPositiveButton("باشه", null).show();
    }
}
