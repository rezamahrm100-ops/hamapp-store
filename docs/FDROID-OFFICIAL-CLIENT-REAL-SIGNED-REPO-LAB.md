# Real official F-Droid client and real disposable signed test repository — hosted emulator

Previous accepted work: genuine official F-Droid APK with pinned upstream GPG signature and Android signing certificate on Android 35, real canonical `fdroidrepos://` deep-link, two actual Gradle debug versions with signature-preserving direct Android upgrade, and separately real fdroidserver signed indexes. These **did not establish that the official F-Droid client actually fetched a newly added signed repository**.

This integration unifies them in one deliberately isolated hosted Android 33 test, using **only generated temporary keys and two actual app debug APKs**.

## Engineered end-to-end path

1. Pinned official `fdroidserver==2.4.5` signs a real HamApp Android v1 package into a real `entry.jar` + `index-v2.json`. `verify_fdroid_private_stage` independently checks the JAR signature, expected temporary repository fingerprint and exact indexed APK digest, version and file bytes.
2. **The signer keystore and config are outside the actual served HTTP webroot.** The program copies only allowlisted repo files under a separate temporary `webroot/fdroid/repo/` directory. It fails on symlinks, hardlinks, unexpected file extensions or unsafe permissions; the private signing config cannot be served.
3. The official F-Droid APK is downloaded from its real upstream, verified by independent GPG and Android developer signing-certificate fingerprint pins, installed onto an isolated hosted Android 33 emulator. A local server on Linux host 127.0.0.1 is accessible to the emulator via Android's 10.0.2.2 host-loopback mapping. It is an **HTTP disposable CI test endpoint**, not a public HTTPS deployment.
4. The emulator sends the officially documented **`fdroidrepo://` scheme for HTTP test repositories** (production HTTPS uses `fdroidrepos://`) with the actual throwaway signer fingerprint to the actual `org.fdroid.fdroid` package. Only nodes actually visible in the official F-Droid app's Android accessibility hierarchy may be tapped. No arbitrary coordinate, forged DB injection or package installation via ADB is counted as in-client app installation.
5. Host server logs only public signed-index request paths and bounded user agents. A success requires actual non-curl/non-Python Android client HTTP requests for `entry.jar`, `index.jar` or `index-v2.json` after the deep link. The lab then adds the actual v2 APK, signs a changed v2 index with the **original** disposable key and requires an independent subsequent real official-client metadata request. Actual signed index hashes must be distinct.
6. On completion the entire signer workspace, private config, debug APKs, official F-Droid downloaded binary and request logs are deleted. Only bounded JSON evidence and isolated emulator screenshots may be uploaded.

## Strict distinction

A successful run would demonstrate **real official-client signed metadata HTTP network access for two successive genuine signed test indexes**, not actual persistent repository subscription, real in-client app v1 install or v2 upgrade, a production HTTPS origin, real owner signer custody, legal publisher identity or phone acceptance. These are separate independently verifiable gates and are deliberately FALSE in the receipt.

The experiment may fail on genuine upstream Android UI onboarding, incompatibility with local HTTP, Android 33 accessibility hierarchy, or the official client's syncing behavior; a failure is **not an accepted integration**. Inspect the exact hosted workflow logs and emulator screenshots, repair as feasible, and never merge as a completed milestone until the full required test is genuinely green. Security-sensitive key material is never uploaded or persisted outside GitHub-hosted temporary disks.

Real F-Droid documentation supports adding user-managed local HTTP repositories during setup and recommends proper HTTPS for actual deployment; official client AndroidManifest declares the custom `fdroidrepo` and `fdroidrepos` intent filters. The test endpoint is `10.0.2.2` only, not a live/public HamApp repository.
