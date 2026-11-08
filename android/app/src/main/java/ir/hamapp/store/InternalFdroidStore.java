package ir.hamapp.store;

import android.app.Activity;
import android.app.AlertDialog;
import android.util.JsonReader;
import android.util.JsonToken;
import android.widget.ProgressBar;

import org.fdroid.index.v2.Entry;
import org.fdroid.index.v2.EntryVerifier;
import org.fdroid.index.IndexParser;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;

import javax.net.ssl.HttpsURLConnection;

import kotlin.Pair;
import kotlin.jvm.functions.Function1;

/**
 * Embedded Android catalogue powered by upstream Apache-2.0 F-Droid index library 0.2.0.
 *
 * SECURITY: fetch and verify entry.jar against an independently pinned repository
 * certificate, then enforce the signed SHA-256 and size of index-v2.json. Only
 * metadata from this signed index may authorize a candidate for the internal
 * installer. F-Droid's unsigned search API is NEVER an install authority.
 *
 * No F-Droid companion application or browser is required.
 */
public final class InternalFdroidStore {
    // F-Droid official default_repos.json X509 certificate; also published on
    // f-droid.org/docs/Release_Channels_and_Signing_Keys/. This is the
    // repository index signer, NOT the HamApp application's debug signing key.
    private static final String FDROID_INDEX_FINGERPRINT =
            "43238d512c1e5eb2d6569f4a3afbf5523418b82e0a3ed1552770abb9a9c9ccab";
    private static final String FDROID_BASE = "https://f-droid.org/repo/";
    private static final int MAX_ENTRY_BYTES = 1024 * 1024;
    private static final long MAX_INDEX_BYTES = 160L * 1024 * 1024;
    private static final int MAX_DISPLAY = 48;
    private static final int MAX_PACKAGES = 16000;
    private static final int MAX_FIELD = 250;

    private InternalFdroidStore() {}

    public static final class Source {
        final String url;
        final String fingerprint;
        final String description;

        private Source(String url, String fingerprint, String description) {
            this.url = url;
            this.fingerprint = fingerprint.toLowerCase(Locale.ROOT);
            this.description = description;
        }

        static Source official() {
            return new Source(FDROID_BASE, FDROID_INDEX_FINGERPRINT, "F-Droid رسمی");
        }

        static Source owner(String url, String fingerprint) {
            if (!RepoPolicy.isAllowed(url, fingerprint))
                throw new IllegalArgumentException("unapproved HamApp repository");
            return new Source(url, fingerprint, "مخزن امضاشدهٔ هَماپ");
        }

        static Source personal(String url, String fingerprint) {
            if (!RepoPolicy.isAllowed(url, fingerprint))
                throw new IllegalArgumentException("invalid personal repository");
            return new Source(url, fingerprint, "مخزن شخصی (مستقل از تأیید ناشر هَماپ)");
        }
    }

    public static final class App {
        public final String id;
        public final String title;
        public final String summary;
        public final long code;
        public final String version;
        public final String apkName;
        public final String apkSha256;
        public final long apkBytes;
        public final List<String> signerSha256;

        App(String id, String title, String summary, Candidate selected) {
            this.id = id;
            this.title = title;
            this.summary = summary;
            this.code = selected.code;
            this.version = selected.version;
            this.apkName = selected.apkName;
            this.apkSha256 = selected.apkSha256;
            this.apkBytes = selected.apkBytes;
            this.signerSha256 = Collections.unmodifiableList(
                    new ArrayList<>(selected.signerSha256));
        }
    }

    private static final class Candidate {
        long code;
        String version = "";
        String apkName = "";
        String apkSha256 = "";
        long apkBytes;
        int minSdk = 1;
        int maxSdk = Integer.MAX_VALUE;
        boolean knownVulnerability;
        boolean unstableChannel;
        List<String> signerSha256 = new ArrayList<>();
        List<String> nativeCode = new ArrayList<>();

        boolean valid() {
            if (code <= 0 || version.isEmpty() || apkBytes < 1 ||
                    apkBytes > EmbeddedApkInstaller.MAX_APK_BYTES ||
                    !validHash(apkSha256) ||
                    !apkName.matches("[A-Za-z0-9_.-]+\\.apk") ||
                    !signerSha256.isEmpty() && signerSha256.size() > 4 ||
                    signerSha256.isEmpty() || knownVulnerability || unstableChannel ||
                    minSdk > android.os.Build.VERSION.SDK_INT ||
                    maxSdk < android.os.Build.VERSION.SDK_INT) return false;
            for (String signer : signerSha256) {
                if (!validHash(signer)) return false;
            }
            if (nativeCode.isEmpty()) return true;
            for (String abi : android.os.Build.SUPPORTED_ABIS) {
                if (nativeCode.contains(abi)) return true;
            }
            return false;
        }
    }

    private static boolean validHash(String value) {
        return value != null && value.matches("[a-fA-F0-9]{64}");
    }

    private static String digest(byte[] bytes) throws Exception {
        return hex(MessageDigest.getInstance("SHA-256").digest(bytes));
    }

    static String hex(byte[] bytes) {
        StringBuilder out = new StringBuilder(bytes.length * 2);
        for (byte b : bytes) out.append(String.format(Locale.ROOT, "%02x", b & 0xff));
        return out.toString();
    }

    private static String shaFile(File file) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        try (InputStream stream = new BufferedInputStream(new FileInputStream(file))) {
            byte[] buf = new byte[65536];
            int count;
            while ((count = stream.read(buf)) != -1) digest.update(buf, 0, count);
        }
        return hex(digest.digest());
    }

    private static String readSmall(InputStream stream) {
        try {
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            byte[] buffer = new byte[8192];
            int length, sum = 0;
            while ((length = stream.read(buffer)) != -1) {
                sum += length;
                if (sum > MAX_ENTRY_BYTES) throw new IOException("signed entry too large");
                out.write(buffer, 0, length);
            }
            return out.toString("UTF-8");
        } catch (IOException ex) {
            throw new IllegalStateException("cannot parse F-Droid signed entry", ex);
        }
    }

    private static void downloadExact(Source source, String path, File target,
            long exactSize, String requiredSha, long maximum) throws Exception {
        if (!path.matches("[A-Za-z0-9_.-]+(?:\\.json|\\.jar|\\.apk)"))
            throw new IOException("invalid signed file path");
        URL address = new URL(source.url + path);
        URL origin = new URL(source.url);
        if (!"https".equals(address.getProtocol()) ||
                !origin.getHost().equalsIgnoreCase(address.getHost()) ||
                !origin.getPath().equals(address.getPath().substring(0, origin.getPath().length())))
            throw new IOException("repository origin changed");
        HttpsURLConnection conn = (HttpsURLConnection) address.openConnection();
        conn.setInstanceFollowRedirects(false);
        conn.setConnectTimeout(12000);
        conn.setReadTimeout(25000);
        conn.setRequestMethod("GET");
        conn.setRequestProperty("Accept", "application/octet-stream");
        long received = 0;
        MessageDigest hash = MessageDigest.getInstance("SHA-256");
        try {
            if (conn.getResponseCode() != 200) throw new IOException("repository HTTP error");
            try (InputStream input = new BufferedInputStream(conn.getInputStream());
                 BufferedOutputStream out = new BufferedOutputStream(new FileOutputStream(target))) {
                byte[] buf = new byte[65536];
                int count;
                while ((count = input.read(buf)) != -1) {
                    received += count;
                    if (received > maximum || (exactSize >= 0 && received > exactSize))
                        throw new IOException("repository file exceeds expected limit");
                    hash.update(buf, 0, count);
                    out.write(buf, 0, count);
                }
            }
            if (received < 1 || (exactSize >= 0 && received != exactSize) ||
                    (requiredSha != null && !hex(hash.digest()).equalsIgnoreCase(requiredSha)))
                throw new IOException("signed repository file hash/size mismatch");
        } catch (Exception ex) {
            target.delete();
            throw ex;
        } finally {
            conn.disconnect();
        }
    }

    /** Always verifies entry.jar with the library's actual JAR-signature verifier. */
    private static Entry signedEntry(Source source, File tmpJar) throws Exception {
        downloadExact(source, "entry.jar", tmpJar, -1, null, MAX_ENTRY_BYTES);
        EntryVerifier upstream = new EntryVerifier(tmpJar, null, source.fingerprint);
        Pair<String, String> checked = upstream.getStreamAndVerify(
                new Function1<InputStream, String>() {
                    @Override public String invoke(InputStream stream) {
                        return readSmall(stream);
                    }
                });
        if (checked.getFirst() == null || checked.getFirst().length() < 512)
            throw new IOException("no trusted repository certificate");
        Entry entry = IndexParser.parseEntry(checked.getSecond());
        if (!"/index-v2.json".equals(entry.getIndex().getName()) ||
                !validHash(entry.getIndex().getSha256()) ||
                entry.getIndex().getSize() <= 0 ||
                entry.getIndex().getSize() > MAX_INDEX_BYTES)
            throw new IOException("invalid signed F-Droid index descriptor");
        return entry;
    }

    private static File verifiedIndex(Activity activity, Source source) throws Exception {
        String fileKey = digest((source.url + source.fingerprint).getBytes(StandardCharsets.UTF_8))
                .substring(0, 16);
        File existing = new File(activity.getFilesDir(), "fdroid-" + fileKey + ".json");
        File signedJar = File.createTempFile("fdroid-entry-", ".jar", activity.getCacheDir());
        try {
            Entry entry = signedEntry(source, signedJar);
            long size = entry.getIndex().getSize();
            String expected = entry.getIndex().getSha256();
            if (existing.isFile() && existing.length() == size &&
                    shaFile(existing).equalsIgnoreCase(expected)) return existing;
            File incoming = File.createTempFile("fdroid-index-", ".json", activity.getFilesDir());
            try {
                downloadExact(source, "index-v2.json", incoming, size, expected, MAX_INDEX_BYTES);
                if (!incoming.renameTo(existing)) {
                    if (!existing.delete() || !incoming.renameTo(existing))
                        throw new IOException("cannot atomically store verified index");
                }
            } finally {
                incoming.delete();
            }
            return existing;
        } finally {
            signedJar.delete();
        }
    }

    private static String localized(JsonReader reader) throws IOException {
        if (reader.peek() != JsonToken.BEGIN_OBJECT) { reader.skipValue(); return ""; }
        String persian = null, english = null, fallback = null;
        reader.beginObject();
        while (reader.hasNext()) {
            String language = reader.nextName();
            if (reader.peek() != JsonToken.STRING) { reader.skipValue(); continue; }
            String value = reader.nextString();
            if (value.isEmpty()) continue;
            if (fallback == null) fallback = value;
            if ("fa".equals(language) || language.startsWith("fa-")) persian = value;
            if ("en".equals(language) || "en-US".equals(language)) english = value;
        }
        reader.endObject();
        String picked = persian != null ? persian : english != null ? english :
                fallback != null ? fallback : "";
        return picked.replace('\n', ' ').replace('\r', ' ').trim()
                .substring(0, Math.min(MAX_FIELD, picked.trim().length()));
    }

    private static String[] metadata(JsonReader reader) throws IOException {
        String[] result = {"", ""};
        reader.beginObject();
        while (reader.hasNext()) {
            String key = reader.nextName();
            if ("name".equals(key)) result[0] = localized(reader);
            else if ("summary".equals(key)) result[1] = localized(reader);
            else reader.skipValue();
        }
        reader.endObject();
        return result;
    }

    private static String textValue(JsonReader reader) throws IOException {
        if (reader.peek() == JsonToken.STRING) return reader.nextString();
        reader.skipValue();
        return "";
    }

    private static void signedFile(JsonReader reader, Candidate candidate) throws IOException {
        reader.beginObject();
        while (reader.hasNext()) {
            String key = reader.nextName();
            if ("name".equals(key)) {
                String name = textValue(reader);
                candidate.apkName = name.startsWith("/") ? name.substring(1) : name;
            } else if ("sha256".equals(key)) candidate.apkSha256 = textValue(reader);
            else if ("size".equals(key)) candidate.apkBytes = reader.nextLong();
            else reader.skipValue();
        }
        reader.endObject();
    }

    private static void manifest(JsonReader reader, Candidate candidate) throws IOException {
        reader.beginObject();
        while (reader.hasNext()) {
            String key = reader.nextName();
            if ("versionCode".equals(key)) candidate.code = reader.nextLong();
            else if ("versionName".equals(key)) candidate.version = textValue(reader);
            else if ("maxSdkVersion".equals(key)) candidate.maxSdk = reader.nextInt();
            else if ("usesSdk".equals(key) && reader.peek() == JsonToken.BEGIN_OBJECT) {
                reader.beginObject();
                while (reader.hasNext()) {
                    String field = reader.nextName();
                    if ("minSdkVersion".equals(field)) candidate.minSdk = reader.nextInt();
                    else reader.skipValue();
                }
                reader.endObject();
            } else if ("signer".equals(key) && reader.peek() == JsonToken.BEGIN_OBJECT) {
                reader.beginObject();
                while (reader.hasNext()) {
                    if ("sha256".equals(reader.nextName()) && reader.peek() == JsonToken.BEGIN_ARRAY) {
                        reader.beginArray();
                        while (reader.hasNext()) {
                            String value = textValue(reader);
                            if (candidate.signerSha256.size() < 8)
                                candidate.signerSha256.add(value.toLowerCase(Locale.ROOT));
                        }
                        reader.endArray();
                    } else reader.skipValue();
                }
                reader.endObject();
            } else if ("nativecode".equals(key) && reader.peek() == JsonToken.BEGIN_ARRAY) {
                reader.beginArray();
                while (reader.hasNext()) {
                    String value = textValue(reader);
                    if (candidate.nativeCode.size() < 20) candidate.nativeCode.add(value);
                }
                reader.endArray();
            } else reader.skipValue();
        }
        reader.endObject();
    }

    private static Candidate version(JsonReader reader) throws IOException {
        Candidate c = new Candidate();
        reader.beginObject();
        while (reader.hasNext()) {
            String key = reader.nextName();
            if ("file".equals(key) && reader.peek() == JsonToken.BEGIN_OBJECT) signedFile(reader, c);
            else if ("manifest".equals(key) && reader.peek() == JsonToken.BEGIN_OBJECT) manifest(reader, c);
            else if ("releaseChannels".equals(key) && reader.peek() == JsonToken.BEGIN_ARRAY) {
                reader.beginArray();
                if (reader.hasNext()) c.unstableChannel = true;
                while (reader.hasNext()) reader.skipValue();
                reader.endArray();
            } else if ("antiFeatures".equals(key) && reader.peek() == JsonToken.BEGIN_OBJECT) {
                reader.beginObject();
                while (reader.hasNext()) {
                    if ("KnownVuln".equals(reader.nextName())) c.knownVulnerability = true;
                    reader.skipValue();
                }
                reader.endObject();
            } else reader.skipValue();
        }
        reader.endObject();
        return c;
    }

    private static App parsePackage(JsonReader reader, String id) throws IOException {
        String title = "", summary = "";
        Candidate best = null;
        reader.beginObject();
        while (reader.hasNext()) {
            String key = reader.nextName();
            if ("metadata".equals(key) && reader.peek() == JsonToken.BEGIN_OBJECT) {
                String[] m = metadata(reader);
                title = m[0];
                summary = m[1];
            } else if ("versions".equals(key) && reader.peek() == JsonToken.BEGIN_OBJECT) {
                reader.beginObject();
                int versionCount = 0;
                while (reader.hasNext()) {
                    reader.nextName();
                    if (++versionCount > 200) {
                        reader.skipValue();
                        continue;
                    }
                    Candidate c = version(reader);
                    if (c.valid() && (best == null || c.code > best.code)) best = c;
                }
                reader.endObject();
            } else reader.skipValue();
        }
        reader.endObject();
        return best == null ? null :
                new App(id, title.isEmpty() ? id : title, summary, best);
    }

    /** Stream the full, hash-verified index without loading ~70MB of JSON into the app heap. */
    private static List<App> matching(File verifiedJson, String requested) throws Exception {
        String query = requested.toLowerCase(Locale.ROOT).trim();
        List<App> found = new ArrayList<>();
        try (JsonReader reader = new JsonReader(
                new InputStreamReader(new BufferedInputStream(
                        new FileInputStream(verifiedJson)), StandardCharsets.UTF_8))) {
            reader.beginObject();
            while (reader.hasNext()) {
                String root = reader.nextName();
                if (!"packages".equals(root) || reader.peek() != JsonToken.BEGIN_OBJECT) {
                    reader.skipValue();
                    continue;
                }
                reader.beginObject();
                int count = 0;
                while (reader.hasNext()) {
                    String id = reader.nextName();
                    if (++count > MAX_PACKAGES) throw new IOException("unbounded repository index");
                    if (!id.matches("[A-Za-z0-9_]+(?:\\.[A-Za-z0-9_]+)+")) {
                        reader.skipValue();
                        continue;
                    }
                    App app = parsePackage(reader, id);
                    if (app != null && (query.isEmpty() ||
                            (app.title + " " + app.id + " " + app.summary)
                                    .toLowerCase(Locale.ROOT).contains(query))) {
                        found.add(app);
                    }
                }
                reader.endObject();
            }
            reader.endObject();
        }
        found.sort((a, b) -> a.title.compareToIgnoreCase(b.title));
        if (found.size() > MAX_DISPLAY) return new ArrayList<>(found.subList(0, MAX_DISPLAY));
        return found;
    }

    private static void details(Activity activity, Source source, App app) {
        String message = "منبع: " + source.description + "\n" +
                "شناسه: " + app.id + "\n" +
                "نسخه: " + app.version + " (" + app.code + ")\n" +
                "اندازهٔ بسته: " + (app.apkBytes / (1024 * 1024)) + " MB\n\n" +
                app.summary + "\n\n" +
                "فهرست مخزن به‌صورت رمزنگاری‌شده اعتبارسنجی شده است؛ " +
                "فایل APK و امضای ناشر آن نیز قبل از درخواست نصب بررسی می‌شوند. " +
                "نصب یا ارتقا فقط با تأیید خود شما و اندروید انجام می‌شود.";
        new AlertDialog.Builder(activity)
                .setTitle(app.title)
                .setMessage(message)
                .setNegativeButton("بستن", null)
                .setPositiveButton("نصب / به‌روزرسانی در هَماپ", (dialog, which) ->
                        EmbeddedApkInstaller.request(activity, source, app))
                .show();
    }

    private static void list(Activity activity, Source source, List<App> apps) {
        if (apps.isEmpty()) {
            new AlertDialog.Builder(activity).setTitle("نتیجه‌ای یافت نشد")
                    .setMessage("در فهرست امضاشده برنامهٔ سازگار با این جست‌وجو پیدا نشد.")
                    .setPositiveButton("بستن", null).show();
            return;
        }
        String[] labels = new String[apps.size()];
        for (int i = 0; i < apps.size(); i++)
            labels[i] = apps.get(i).title + " — " + apps.get(i).id;
        new AlertDialog.Builder(activity)
                .setTitle(source.description + " | برنامه‌های سازگار")
                .setItems(labels, (dialog, index) -> details(activity, source, apps.get(index)))
                .setNegativeButton("بستن", null).show();
    }

    private static void begin(Activity activity, Source source, String query) {
        ProgressBar bar = new ProgressBar(activity);
        bar.setPadding(36, 24, 36, 24);
        AlertDialog progress = new AlertDialog.Builder(activity)
                .setTitle("اعتبارسنجی و بارگذاری مخزن امضاشده")
                .setView(bar).setCancelable(false).create();
        progress.show();
        new Thread(() -> {
            List<App> matched = null;
            String error = null;
            try {
                matched = matching(verifiedIndex(activity, source), query);
            } catch (Exception ex) {
                error = "مخزن قابل دریافت یا امضای آن قابل تأیید نبود؛ هیچ بسته‌ای قابل نصب نیست.";
            }
            final List<App> results = matched;
            final String problem = error;
            activity.runOnUiThread(() -> {
                progress.dismiss();
                if (activity.isFinishing() || activity.isDestroyed()) return;
                if (problem != null) {
                    new AlertDialog.Builder(activity).setTitle("مخزن تأیید نشد")
                            .setMessage(problem).setPositiveButton("بستن", null).show();
                } else list(activity, source, results);
            });
        }, "hamapp-signed-fdroid-index").start();
    }

    public static void openPublic(Activity activity, String raw) {
        String query = raw == null ? "" : raw.trim();
        if (query.length() > 80 || query.indexOf('\n') >= 0 || query.indexOf('\r') >= 0) {
            new AlertDialog.Builder(activity).setMessage("عبارت جست‌وجو نامعتبر است.")
                    .setPositiveButton("بستن", null).show();
            return;
        }
        new AlertDialog.Builder(activity)
                .setTitle("فروشگاه F-Droid داخل هَماپ")
                .setMessage("فهرست عمومی رسمی (~۷۰ مگابایت بار اول) پس از بررسی امضای مخزن دریافت می‌شود. " +
                        "نصب‌کنندهٔ خارجی F-Droid لازم نیست. " +
                        "در صورت ادامه، اتصال اینترنت و فضای ذخیره‌سازی مصرف می‌شود. " +
                        "نصب هر برنامه جداگانه تأیید خواهد شد.")
                .setNegativeButton("لغو", null)
                .setPositiveButton("بارگذاری در هَماپ", (d, w) ->
                        begin(activity, Source.official(), query)).show();
    }

    public static void openApproved(Activity activity, org.json.JSONObject approved) {
        try {
            Source source = Source.owner(
                    approved.getString("url"), approved.getString("fingerprint"));
            new AlertDialog.Builder(activity)
                    .setTitle("مخزن اختصاصی هَماپ")
                    .setMessage("فهرست مخزن اختصاصی فقط پس از بررسی امضای ثبت‌شده باز خواهد شد. ادامه؟")
                    .setNegativeButton("لغو", null)
                    .setPositiveButton("ادامه", (d, w) -> begin(activity, source, ""))
                    .show();
        } catch (Exception ex) {
            new AlertDialog.Builder(activity).setTitle("مخزن نامعتبر")
                    .setMessage("هویت مخزن ناشر تأیید نشده است.")
                    .setPositiveButton("بستن", null).show();
        }
    }
    public static void openSubscribed(Activity activity, String url,
            String fingerprint, String search) {
        try {
            String query = search == null ? "" : search.trim();
            if (query.length() > 80 || query.indexOf('\n') >= 0 || query.indexOf('\r') >= 0)
                throw new IllegalArgumentException("invalid query");
            Source source = Source.personal(url, fingerprint);
            new AlertDialog.Builder(activity)
                    .setTitle("اتصال به مخزن شخصی")
                    .setMessage("اثر انگشت ارائه‌شده توسط شما برای بررسی رمزنگاری‌شدهٔ مخزن " +
                            "استفاده می‌شود. هَماپ اعتبار مستقل ناشر شخصی را تأیید نکرده است. " +
                            "فهرست فقط پس از بررسی امضای مطابق اثرانگشت بارگذاری می‌شود.")
                    .setNegativeButton("لغو", null)
                    .setPositiveButton("بررسی و نمایش", (d, which) -> begin(activity, source, query))
                    .show();
        } catch (IllegalArgumentException ex) {
            new AlertDialog.Builder(activity).setTitle("مخزن شخصی نامعتبر")
                    .setMessage("نشانی و اثر انگشت را در تنظیمات اصلاح کنید.")
                    .setPositiveButton("بستن", null).show();
        }
    }

}
