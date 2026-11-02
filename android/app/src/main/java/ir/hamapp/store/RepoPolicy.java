package ir.hamapp.store;

import android.net.Uri;
import java.util.Locale;
import java.util.regex.Pattern;

/** Prevent arbitrary webpage or unsigned repository handoff. */
public final class RepoPolicy {
    private static final Pattern FP = Pattern.compile("^[0-9A-Fa-f]{64}$");
    private RepoPolicy() {}

    public static boolean isAllowed(String raw, String fingerprint) {
        if (raw == null || fingerprint == null || !FP.matcher(fingerprint).matches()) return false;
        if (raw.length() > 2048 || raw.indexOf('\\') >= 0 || raw.indexOf('\r') >= 0
                || raw.indexOf('\n') >= 0 || raw.indexOf('%') >= 0) return false;
        Uri uri = Uri.parse(raw);
        String host = uri.getHost();
        return "https".equals(uri.getScheme())
                && host != null && host.indexOf('.') > 0
                && uri.getUserInfo() == null
                && uri.getPort() == -1
                && uri.getQuery() == null
                && uri.getFragment() == null
                && "/fdroid/repo/".equals(uri.getPath())
                && raw.equals("https://" + host.toLowerCase(Locale.ROOT) + "/fdroid/repo/");
    }
}
