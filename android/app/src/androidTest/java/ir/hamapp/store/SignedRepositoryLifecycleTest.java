package ir.hamapp.store;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

import android.app.Activity;
import android.content.Context;
import android.content.SharedPreferences;

import androidx.test.core.app.ActivityScenario;
import androidx.test.ext.junit.runners.AndroidJUnit4;

import org.junit.Test;
import org.junit.runner.RunWith;

import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.util.List;

/**
 * Ephemeral Android 35 instrumentation: real Android private preferences,
 * no network access, no user apps installed, no fake approval identities.
 */
@RunWith(AndroidJUnit4.class)
public final class SignedRepositoryLifecycleTest {
    private static final String A = "https://alpha.example.org/fdroid/repo/";
    private static final String B = "https://beta.example.org/fdroid/repo/";
    private static final String C = "https://gamma.example.org/fdroid/repo/";
    private static final String PIN_A =
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
    private static final String PIN_B =
            "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
    private static final String PIN_C =
            "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc";

    private void run(Work test) {
        try (ActivityScenario<MainActivity> scenario = ActivityScenario.launch(MainActivity.class)) {
            scenario.onActivity(activity -> {
                SharedPreferences prefs = activity.getSharedPreferences(
                        "personal_fdroid_repo_v1", Context.MODE_PRIVATE);
                assertTrue("test data reset failed", prefs.edit().clear().commit());
                try {
                    test.check(activity, prefs);
                } finally {
                    prefs.edit().clear().commit();
                    InternalFdroidStore.dropCache(activity, A, PIN_A);
                    InternalFdroidStore.dropCache(activity, B, PIN_B);
                    InternalFdroidStore.dropCache(activity, C, PIN_C);
                }
            });
        }
    }

    private interface Work {
        void check(Activity activity, SharedPreferences prefs);
    }

    @Test public void independentRepositoriesKeepSeparatePinsAndDeletion() {
        run((activity, prefs) -> {
            UserRepoSettings.addForUser(activity, A, PIN_A);
            UserRepoSettings.addForUser(activity, B, PIN_B);
            List<UserRepoSettings.Repository> sources = UserRepoSettings.saved(activity);
            assertEquals(2, sources.size());
            assertEquals(A, sources.get(0).url);
            assertEquals(PIN_B, sources.get(1).fingerprint);
            assertTrue(UserRepoSettings.configured(activity));
            assertFalse(prefs.getString("signed_repositories_v2", "").contains("PRIVATE KEY"));
            // An in-place signer change is never interpreted as a safe update.
            try {
                UserRepoSettings.addForUser(activity, A, PIN_C);
                fail("pin switch accepted");
            } catch (IllegalArgumentException expected) {
                assertEquals(2, UserRepoSettings.saved(activity).size());
            }
            UserRepoSettings.removeForUser(activity, sources.get(0));
            assertEquals(1, UserRepoSettings.saved(activity).size());
            assertEquals(B, UserRepoSettings.saved(activity).get(0).url);
            try {
                UserRepoSettings.removeForUser(activity, sources.get(0));
                fail("missing repository removed twice");
            } catch (IllegalArgumentException expected) {
                assertEquals(1, UserRepoSettings.saved(activity).size());
            }
        });
    }

    @Test public void legacySingleRepositoryMigratesWithoutChangingItsPin() {
        run((activity, prefs) -> {
            assertTrue(prefs.edit().putString("repository_url", A)
                    .putString("trusted_index_fingerprint", PIN_A).commit());
            assertEquals(1, UserRepoSettings.saved(activity).size());
            UserRepoSettings.addForUser(activity, C, PIN_C);
            assertEquals(2, UserRepoSettings.saved(activity).size());
            assertEquals(PIN_A, UserRepoSettings.saved(activity).get(0).fingerprint);
            assertFalse(prefs.contains("repository_url"));
            assertFalse(prefs.contains("trusted_index_fingerprint"));
        });
    }

    @Test public void unsafeOrCorruptTrustStateFailsClosed() {
        run((activity, prefs) -> {
            try {
                UserRepoSettings.addForUser(activity, "http://unsafe.example.org/fdroid/repo/", PIN_A);
                fail("HTTP accepted");
            } catch (IllegalArgumentException expected) {
                assertFalse(UserRepoSettings.configured(activity));
            }
            assertTrue(prefs.edit().putString("signed_repositories_v2",
                    "[{\"url\":\"" + A + "\",\"fingerprint\":\"" + PIN_A + "\"}," +
                    "{\"url\":\"" + A + "\",\"fingerprint\":\"" + PIN_B + "\"}]").commit());
            try {
                UserRepoSettings.saved(activity);
                fail("ambiguous duplicate repo identity accepted");
            } catch (IllegalStateException expected) {
                assertFalse(UserRepoSettings.configured(activity));
            }
        });
    }

    @Test public void offlineIndexWithNoVerifiedReceiptNeverOpens() {
        run((activity, prefs) -> {
            try {
                Method read = InternalFdroidStore.class.getDeclaredMethod(
                        "verifiedOfflineIndex", Activity.class,
                        InternalFdroidStore.Source.class);
                read.setAccessible(true);
                read.invoke(null, activity, InternalFdroidStore.Source.personal(A, PIN_A));
                fail("unverified offline catalogue opened");
            } catch (InvocationTargetException expected) {
                assertTrue(expected.getCause() instanceof IOException);
            } catch (ReflectiveOperationException error) {
                throw new AssertionError("offline cache contract missing", error);
            }
        });
    }
}
