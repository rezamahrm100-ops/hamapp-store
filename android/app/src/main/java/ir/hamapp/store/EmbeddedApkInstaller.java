package ir.hamapp.store;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.app.PendingIntent;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.content.pm.PackageInstaller;
import android.content.pm.PackageManager;
import android.content.pm.Signature;
import android.net.Uri;
import android.os.Build;
import android.provider.Settings;
import android.widget.ProgressBar;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.net.URL;
import java.security.MessageDigest;
import java.util.HashSet;
import java.util.Locale;
import java.util.Set;
import java.util.concurrent.atomic.AtomicBoolean;

import javax.net.ssl.HttpsURLConnection;

/**
 * Embedded consent-based Android installer: verified APK -> OS PackageInstaller.
 *
 * Never installs directly from a search result. Source repository index must
 * already be JAR-signature-verified and the APK digest and manifest signing
 * certificate must both match the entry in that signed index.
 */
public final class EmbeddedApkInstaller {
    static final long MAX_APK_BYTES = 512L * 1024 * 1024;
    private static final AtomicBoolean ACTIVE = new AtomicBoolean(false);

    private EmbeddedApkInstaller() {}

    private static boolean matchesPackage(String id) {
        return id != null && id.matches("[A-Za-z0-9_]+(?:\\.[A-Za-z0-9_]+)+");
    }

    private static void checkPermission(Activity activity) {
        if (Build.VERSION.SDK_INT < 28)
            throw new IllegalStateException("Secure APK signer inspection requires Android 9+");
        if (!activity.getPackageManager().canRequestPackageInstalls())
            throw new SecurityException("permission required");
    }

    private static File verifiedApk(Activity activity, InternalFdroidStore.Source source,
            InternalFdroidStore.App app, AtomicBoolean cancelled) throws Exception {
        if (!matchesPackage(app.id) || !app.apkName.matches("[A-Za-z0-9_.-]+\\.apk") ||
                app.apkBytes < 1 || app.apkBytes > MAX_APK_BYTES ||
                !app.apkSha256.matches("[0-9a-fA-F]{64}"))
            throw new IOException("unsafe signed package metadata");
        URL base = new URL(source.url);
        URL location = new URL(source.url + app.apkName);
        if (!"https".equals(location.getProtocol()) ||
                !base.getHost().equalsIgnoreCase(location.getHost()) ||
                !location.getPath().startsWith(base.getPath()))
            throw new IOException("package redirected away from verified repository");
        File file = File.createTempFile("hamapp-verified-", ".apk", activity.getCacheDir());
        HttpsURLConnection conn = (HttpsURLConnection) location.openConnection();
        conn.setConnectTimeout(14000);
        conn.setReadTimeout(30000);
        conn.setInstanceFollowRedirects(false);
        conn.setRequestMethod("GET");
        long total = 0;
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        try {
            if (conn.getResponseCode() != 200) throw new IOException("APK download failed");
            try (InputStream input = new BufferedInputStream(conn.getInputStream());
                 OutputStream output = new BufferedOutputStream(new FileOutputStream(file))) {
                byte[] buffer = new byte[65536];
                int n;
                while ((n = input.read(buffer)) != -1) {
                    if (cancelled.get()) throw new IOException("download cancelled");
                    total += n;
                    if (total > app.apkBytes || total > MAX_APK_BYTES)
                        throw new IOException("APK exceeds signed size");
                    digest.update(buffer, 0, n);
                    output.write(buffer, 0, n);
                }
            }
            if (total != app.apkBytes ||
                    !InternalFdroidStore.hex(digest.digest()).equalsIgnoreCase(app.apkSha256))
                throw new IOException("APK digest does not match signed repository");
            validateApk(activity, file, app);
            return file;
        } catch (Exception ex) {
            file.delete();
            throw ex;
        } finally {
            conn.disconnect();
        }
    }

    private static void validateApk(Activity activity, File file,
            InternalFdroidStore.App app) throws Exception {
        PackageManager pm = activity.getPackageManager();
        PackageInfo archive = pm.getPackageArchiveInfo(
                file.getAbsolutePath(), PackageManager.GET_SIGNING_CERTIFICATES);
        if (archive == null || !app.id.equals(archive.packageName) ||
                archive.getLongVersionCode() != app.code ||
                archive.signingInfo == null)
            throw new IOException("APK package identity or version mismatch");

        Signature[] signers = archive.signingInfo.getApkContentsSigners();
        if (signers == null || signers.length < 1 ||
                signers.length != app.signerSha256.size())
            throw new IOException("APK signer count differs from signed index");
        Set<String> pinned = new HashSet<>(app.signerSha256);
        for (Signature signer : signers) {
            String certificate = InternalFdroidStore.hex(
                    MessageDigest.getInstance("SHA-256").digest(signer.toByteArray()));
            if (!pinned.remove(certificate.toLowerCase(Locale.ROOT)))
                throw new IOException("APK publisher signing certificate mismatch");
        }
        if (!pinned.isEmpty()) throw new IOException("missing expected APK publisher");

        // Installed-version preflight, where package visibility allows it.
        // Android's OS installer independently enforces signer and downgrade
        // checks even when an installed package is invisible to this app.
        try {
            PackageInfo installed = pm.getPackageInfo(app.id, 0);
            if (installed.getLongVersionCode() >= app.code)
                throw new IOException("installed application is up-to-date or newer");
        } catch (PackageManager.NameNotFoundException notInstalledOrVisible) {
            // No existing package visible. OS session still validates update.
        }
    }

    private static void commit(Activity activity, File verified, InternalFdroidStore.App app)
            throws Exception {
        PackageInstaller manager = activity.getPackageManager().getPackageInstaller();
        PackageInstaller.SessionParams params = new PackageInstaller.SessionParams(
                PackageInstaller.SessionParams.MODE_FULL_INSTALL);
        params.setAppPackageName(app.id);
        params.setSize(app.apkBytes);
        int id = manager.createSession(params);
        boolean committed = false;
        try (PackageInstaller.Session session = manager.openSession(id)) {
            // Session.commit() MUST run after every session output stream
            // has been closed, otherwise Android rejects the transaction.
            try (InputStream input = new BufferedInputStream(new FileInputStream(verified));
                 OutputStream output = session.openWrite("base.apk", 0, app.apkBytes)) {
                byte[] buf = new byte[65536];
                int n;
                while ((n = input.read(buf)) != -1) output.write(buf, 0, n);
                session.fsync(output);
            }
            Intent callback = new Intent(activity, InstallResultActivity.class);
            callback.setAction("ir.hamapp.store.INSTALL_COMPLETED");
            callback.putExtra("expected_package", app.id);
            int flags = PendingIntent.FLAG_UPDATE_CURRENT;
            if (Build.VERSION.SDK_INT >= 31) flags |= PendingIntent.FLAG_MUTABLE;
            PendingIntent pending = PendingIntent.getActivity(activity, id, callback, flags);
            session.commit(pending.getIntentSender());
            committed = true;
        } finally {
            if (!committed) manager.abandonSession(id);
        }
    }

    public static void request(Activity activity, InternalFdroidStore.Source source,
            InternalFdroidStore.App app) {
        if (source.personal && !UserRepoSettings.isRegistered(
                activity, source.url, source.fingerprint)) {
            new AlertDialog.Builder(activity).setTitle("اعتماد به مخزن حذف شده")
                    .setMessage("برای نصب باید مخزن امضاشده همچنان در تنظیمات ثبت باشد.")
                    .setPositiveButton("بستن", null).show();
            return;
        }
        if (!ACTIVE.compareAndSet(false, true)) {
            new AlertDialog.Builder(activity).setMessage("عملیات نصب قبلی هنوز فعال است.")
                    .setPositiveButton("باشه", null).show();
            return;
        }
        try {
            checkPermission(activity);
        } catch (SecurityException ex) {
            ACTIVE.set(false);
            new AlertDialog.Builder(activity)
                    .setTitle("اجازهٔ نصب از هَماپ")
                    .setMessage("اندروید باید یک‌بار اجازهٔ نصب برنامه از این منبع را صادر کند. " +
                            "این مجوز نصب خودکار نمی‌دهد؛ هر برنامه باز هم تأیید جداگانه دارد.")
                    .setNegativeButton("لغو", null)
                    .setPositiveButton("تنظیمات اندروید", (d,w) -> {
                        Intent intent = new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
                                Uri.parse("package:" + activity.getPackageName()));
                        activity.startActivity(intent);
                    }).show();
            return;
        } catch (IllegalStateException ex) {
            ACTIVE.set(false);
            new AlertDialog.Builder(activity).setMessage(ex.getMessage())
                    .setPositiveButton("باشه", null).show();
            return;
        }
        AtomicBoolean cancelled = new AtomicBoolean(false);
        ProgressBar spinner = new ProgressBar(activity);
        spinner.setPadding(30, 24, 30, 24);
        AlertDialog dialog = new AlertDialog.Builder(activity)
                .setTitle("دریافت و اعتبارسنجی " + app.title)
                .setMessage("در حال بررسی SHA-256 و امضای ناشر؛ امکان لغو وجود دارد.")
                .setView(spinner)
                .setNegativeButton("لغو", (d,w) -> cancelled.set(true))
                .create();
        dialog.show();
        new Thread(() -> {
            String error = null;
            File file = null;
            try {
                file = verifiedApk(activity, source, app, cancelled);
                if (cancelled.get()) throw new IOException("cancelled");
                if (source.personal && !UserRepoSettings.isRegistered(
                        activity, source.url, source.fingerprint))
                    throw new IOException("personal repository trust was removed");
                commit(activity, file, app);
            } catch (Exception ex) {
                error = "بسته دریافت یا اعتبارسنجی/نصب نشد؛ هَماپ هیچ بستهٔ تأییدنشده‌ای نصب نمی‌کند.";
            } finally {
                if (file != null) file.delete();
                ACTIVE.set(false);
            }
            String problem = error;
            activity.runOnUiThread(() -> {
                dialog.dismiss();
                if (activity.isFinishing() || activity.isDestroyed()) return;
                if (problem != null && !cancelled.get())
                    new AlertDialog.Builder(activity).setTitle("عملیات متوقف شد")
                            .setMessage(problem).setPositiveButton("باشه", null).show();
            });
        }, "hamapp-verified-apk-installer").start();
    }
}
