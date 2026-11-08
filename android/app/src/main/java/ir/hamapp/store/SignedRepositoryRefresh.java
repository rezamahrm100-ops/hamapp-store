package ir.hamapp.store;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.content.SharedPreferences;

import androidx.annotation.NonNull;
import androidx.work.BackoffPolicy;
import androidx.work.Constraints;
import androidx.work.ExistingPeriodicWorkPolicy;
import androidx.work.ExistingWorkPolicy;
import androidx.work.NetworkType;
import androidx.work.OneTimeWorkRequest;
import androidx.work.PeriodicWorkRequest;
import androidx.work.Worker;
import androidx.work.WorkerParameters;
import androidx.work.WorkManager;
import androidx.work.Data;

import java.text.DateFormat;
import java.util.Date;
import java.util.List;
import java.util.concurrent.TimeUnit;

/**
 * Opt-in daily catalogue verification using WorkManager's durable scheduling.
 * No APK downloads, installations, automatic OS install requests, publisher
 * approvals, notifications or private signing keys are handled in this worker.
 * Network constraints: unmetered and battery not low.
 */
public final class SignedRepositoryRefresh extends Worker {
    private static final String PREFS = "signed_repo_background_refresh_v1";
    private static final String ENABLED = "enabled";
    private static final String LAST_SUCCESS = "last_success_ms";
    private static final String LAST_COUNT = "last_verified_sources";
    private static final String STATUS = "state";
    private static final String UNIQUE_PERIODIC = "hamapp-signed-repositories-daily-v1";
    private static final String UNIQUE_MANUAL = "hamapp-signed-repositories-user-check-v1";
    private static final String USER_REQUESTED = "explicit_user_request";
    private static final int HOURS = 24;

    public SignedRepositoryRefresh(@NonNull Context context,
            @NonNull WorkerParameters parameters) {
        super(context, parameters);
    }

    private static SharedPreferences settings(Context context) {
        return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    static boolean enabled(Context context) {
        return settings(context).getBoolean(ENABLED, false);
    }

    private static Constraints networkConstraints() {
        return new Constraints.Builder()
                .setRequiredNetworkType(NetworkType.UNMETERED)
                .setRequiresBatteryNotLow(true)
                .build();
    }

    private static void schedule(Context context) {
        PeriodicWorkRequest request = new PeriodicWorkRequest.Builder(
                SignedRepositoryRefresh.class, HOURS, TimeUnit.HOURS)
                .setConstraints(networkConstraints())
                .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 30, TimeUnit.MINUTES)
                .build();
        WorkManager.getInstance(context).enqueueUniquePeriodicWork(
                UNIQUE_PERIODIC, ExistingPeriodicWorkPolicy.UPDATE, request);
    }

    static void configure(Context context, boolean value) {
        // Consent is persisted privately before scheduling, never assumed
        // from app installation, system boot or merely connecting a repo.
        if (!settings(context).edit().putBoolean(ENABLED, value).commit())
            throw new IllegalStateException("periodic refresh preference could not be stored");
        if (value) {
            try {
                schedule(context);
            } catch (RuntimeException failure) {
                settings(context).edit().putBoolean(ENABLED, false).commit();
                throw failure;
            }
        } else {
            WorkManager.getInstance(context).cancelUniqueWork(UNIQUE_PERIODIC);
            WorkManager.getInstance(context).cancelUniqueWork(UNIQUE_MANUAL);
        }
    }

    static void reconcile(Context context) {
        if (enabled(context)) schedule(context);
        else WorkManager.getInstance(context).cancelUniqueWork(UNIQUE_PERIODIC);
    }

    private static void checkNow(Context context) {
        OneTimeWorkRequest request = new OneTimeWorkRequest.Builder(
                SignedRepositoryRefresh.class)
                .setInputData(new Data.Builder().putBoolean(USER_REQUESTED, true).build())
                .setConstraints(networkConstraints())
                .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 30, TimeUnit.MINUTES)
                .build();
        WorkManager.getInstance(context).enqueueUniqueWork(
                UNIQUE_MANUAL, ExistingWorkPolicy.KEEP, request);
    }

    public static void openSettings(Activity activity) {
        SharedPreferences p = settings(activity);
        boolean active = enabled(activity);
        long latest = p.getLong(LAST_SUCCESS, 0);
        String last = latest == 0 ? "هنوز هیچ بررسی موفقی ثبت نشده است."
                : "آخرین بررسی موفق: " +
                    DateFormat.getDateTimeInstance().format(new Date(latest)) +
                    " | مخزن‌ها: " + p.getInt(LAST_COUNT, 0);
        String status = p.getString(STATUS, "");
        String message = "هر ۲۴ ساعت، فقط با اینترنت نامحدود و باتری کافی، امضای " +
                "مخزن‌های شخصی ثبت‌شده و فایل فهرست آن‌ها دوباره بررسی می‌شود.\n" +
                "نصب خودکار، دانلود APK، تغییر کلید امضا یا انتشار عمومی انجام نمی‌شود.\n" +
                "زمان‌بندی توسط اندروید انجام می‌شود و ممکن است با تأخیر اجرا شود.\n\n" +
                "وضعیت: " + (active ? "فعال" : "غیرفعال") + "\n" + last +
                (status.isEmpty() ? "" : "\nنتیجهٔ آخر: " +
                    ("verified".equals(status) ? "تأیید موفق" :
                     "retry".equals(status) ? "اختلال شبکه؛ تلاش مجدد برنامه‌ریزی شد" :
                     "blocked".equals(status) ? "مخزن یا امضا تأیید نشد" : "در حال بررسی"));
        new AlertDialog.Builder(activity)
                .setTitle("بررسی دوره‌ای مخزن‌های امضاشده")
                .setMessage(message)
                .setNegativeButton("بستن", null)
                .setNeutralButton("بررسی اکنون", (d, w) -> {
                    checkNow(activity);
                    new AlertDialog.Builder(activity)
                            .setTitle("درخواست بررسی ثبت شد")
                            .setMessage("بررسی فقط با اینترنت نامحدود و باتری کافی اجرا می‌شود؛ " +
                                    "هیچ برنامه‌ای خودکار نصب نخواهد شد.")
                            .setPositiveButton("بستن", null).show();
                })
                .setPositiveButton(active ? "غیرفعال‌سازی" : "فعال‌سازی روزانه",
                        (d, w) -> {
                            try {
                                configure(activity, !active);
                                openSettings(activity);
                            } catch (RuntimeException error) {
                                new AlertDialog.Builder(activity)
                                        .setTitle("زمان‌بندی ثبت نشد")
                                        .setMessage("سرویس بررسی دوره‌ای در این دستگاه در دسترس نیست.")
                                        .setPositiveButton("بستن", null).show();
                            }
                        }).show();
    }

    @NonNull
    @Override
    public Result doWork() {
        Context ctx = getApplicationContext();
        if (!enabled(ctx) && !getInputData().getBoolean(USER_REQUESTED, false))
            return Result.success();
        int checked = 0;
        try {
            List<UserRepoSettings.Repository> sources = UserRepoSettings.saved(ctx);
            for (UserRepoSettings.Repository repository : sources) {
                if (isStopped()) return Result.retry();
                if (!enabled(ctx) && !getInputData().getBoolean(USER_REQUESTED, false))
                    return Result.success();
                // Only the signed-index verifier receives network bytes.
                // It rechecks the owner's active fingerprint before commit.
                InternalFdroidStore.refreshSubscribed(ctx,
                        repository.url, repository.fingerprint);
                checked++;
            }
            if (!settings(ctx).edit().putInt(LAST_COUNT, checked)
                    .putLong(LAST_SUCCESS, System.currentTimeMillis())
                    .putString(STATUS, "verified").commit())
                return Result.retry();
            return Result.success();
        } catch (IllegalArgumentException | IllegalStateException failure) {
            settings(ctx).edit().putString(STATUS, "blocked").commit();
            return Result.failure();
        } catch (Exception error) {
            // A failed signature/download never publishes new metadata and
            // never falls back to unsigned or stale content for installation.
            settings(ctx).edit().putString(STATUS, "retry").commit();
            return Result.retry();
        }
    }
}
