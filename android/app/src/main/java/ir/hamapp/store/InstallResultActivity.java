package ir.hamapp.store;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.pm.PackageInstaller;
import android.os.Bundle;

/** Private explicit system-installer result callback; no external app handler. */
public final class InstallResultActivity extends Activity {
    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        Intent result = getIntent();
        int status = result.getIntExtra(PackageInstaller.EXTRA_STATUS,
                PackageInstaller.STATUS_FAILURE);
        if (status == PackageInstaller.STATUS_PENDING_USER_ACTION) {
            try {
                Intent confirmation = result.getParcelableExtra(Intent.EXTRA_INTENT);
                if (confirmation == null) throw new IllegalStateException();
                startActivity(confirmation);
            } catch (RuntimeException ex) {
                new AlertDialog.Builder(this)
                        .setTitle("تأیید نصب در دسترس نیست")
                        .setPositiveButton("بستن", (d,w) -> finish()).show();
                return;
            }
            finish();
            return;
        }
        String text = status == PackageInstaller.STATUS_SUCCESS ?
                "اندروید نصب یا به‌روزرسانی بسته را تأیید کرد." :
                "نصب به‌وسیلهٔ اندروید تأیید نشد یا توسط کاربر لغو شد.";
        new AlertDialog.Builder(this)
                .setTitle("نتیجهٔ نصب در هَماپ")
                .setMessage(text)
                .setPositiveButton("بستن", (d,w) -> finish()).show();
    }
}
