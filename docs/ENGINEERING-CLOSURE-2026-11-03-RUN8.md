# HamApp — integrated engineering RUN8, 2026-11-03

**This is a facts ledger, not a publication approval.** Always re-read live main, exact-head GitHub checks, current PRs and owner runner. Product-wide engineering **PARTIAL**, production release **BLOCKED**.

## Three integrated engineering merges accepted on real GitHub CI

### PR #59 — actual TLS remote publisher quarantine

- [PR #59](https://github.com/rezamahrm100-ops/hamapp-store/pull/59) merged main `33a18fcbe713cea5416bdd6f8b1f28ef12129b42`; accepted head `00e87c398212d6585a960b8d47d8c7f1e2875955`.
- Real `scripts/remote_publisher_tls_service.py` uses actual HTTPS TLS1.2+ on owner-POSIX, 0600 private cert/key and token-hash registry, private per-tenant exact-byte binary quarantine with bounded socket threads, owner-bounded uploads and serial quota. Explicit opt-in required for public-interface bind. Remote `scripts/remote_publisher_submit.py` checks TLS CA/hostname and **independently approved leaf SHA-256 BEFORE reading or sending bearer credential**, reuses existing exact-byte streaming upload and no-approve receipt. Real locally generated OpenSSL private key/cert/HTTPS socket tests include bad TLS pin/CA, plaintext downgrade, wrong tenant/token, unsafe key permissions, actual file bytes/permissions and remote review denial. Nothing was deployed to public DNS or a VPS; no identity/MFA/payment/approval/public release.
- Final feature head hosted CI #41614033641, CodeQL #41614033494, Trivy #41614033455 **SUCCESS**. See [docs/REMOTE-PUBLISHER-TLS-QUARANTINE.md](REMOTE-PUBLISHER-TLS-QUARANTINE.md). Do not confuse an authenticated transport token with an independently verified developer identity.

### PR #60 — F-Droid canonical repository URI functional bug fixed

- [PR #60](https://github.com/rezamahrm100-ops/hamapp-store/pull/60) merged `c437292514504114f8852ebb49d0bb21c596ee32`; feature final head `6e13a281eaef1126ead60143db6b242b14278941`.
- Previous Android native app incorrectly concatenated `fdroidrepos://` and a full `https://domain/fdroid/repo/` URL, resulting in a malformed URI with hostname `https`, despite a real F-Droid activity launch. Native app now **replaces** the scheme using `Uri.parse(url).buildUpon().scheme("fdroidrepos")`, preserving approved host, path, actual fingerprint, explicit Android user confirmation and separate fixed allowlist `RepoPolicy`. Isolated official-client emulator test uses canonical `fdroidrepos://example.invalid/...` without adding an untrusted repo.
- **ALL EIGHT** exact-head hosted checks **SUCCESS**: CI #41614704494, CodeQL #41614704520, Trivy #41614704544, Android APK #41614704376, ClamAV #41614704630, emulator UI smoke #41614704703, actual two-debug-version upgrade #41614704518 and official F-Droid pinned GPG+Android cert client emulator #41614704756. **Real F-Droid repository subscription, APK download/install and app update are NOT proved**.

### PR #61 — actual hosted Windows NSIS per-user installer lifecycle

- [PR #61](https://github.com/rezamahrm100-ops/hamapp-store/pull/61) merged `c53f6f1403d5836882238a980003a4f517e4fdfc`; accepted source head `079f49a0203fff96a326c119791877487fb16c3b`.
- Real free/open-source NSIS 3.11.0 builds **two genuine unsigned installer versions** wrapping the **exact same native Windows PyInstaller EXE** obtained from the hosted Windows build artifact. On a disposable GitHub-hosted Windows Server 2022, PowerShell actually executed v1 install and verified real HKCU version/EXE SHA, actual v2 installer upgrade/registry version, real v1 downgrade refusal without changing installed EXE, real uninstaller and cleanup of per-user app folder/registry. All test installer binaries remained inside runner-temp, not publicly distributed.
- Actual [workflow #41615744172](https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41615744172) **SUCCESS**, including Windows `desktop-preview`, `nsis-installer-sandbox` and separate genuine Linux PE portable Authenticode (two disposable signers, negative signed/unsigned/tamper). Log includes `NSIS_REAL_SANDBOX_VERSION1_INSTALL`, `VERSION2_UPGRADE`, `DOWNGRADE_REJECTION`, `UNINSTALL` and final `ACTUAL_WINDOWS_NSIS_INSTALL_UPGRADE_DENY_DOWNGRADE_UNINSTALL_ACCEPTED`. Short-lived bounded receipt `hamapp-real-hosted-nsis-install-qa`, ID `13220907662`. Source CI #41615744352, CodeQL #41615744274 and Trivy #41615744221 **SUCCESS**.
- **Not verified**: differing v2 *app binary*, signed MSI/MSIX or commercial CA/SmartScreen/WinGet registry, Windows system-wide elevation/UAC/owner physical-device install. NSIS v2 means installer **version**, not two different app builds. See [docs/WINDOWS-NSIS-INSTALLER-REAL-QA.md](WINDOWS-NSIS-INSTALLER-REAL-QA.md).

## Verified latest main from source merges

Main at initial RUN8 handoff: `c53f6f1403d5836882238a980003a4f517e4fdfc`. At the last live check, SIX associated GitHub-hosted checks **SUCCESS**: CI #41616063504, CodeQL #41616063086, Trivy #41616063099, Pages #41616062959, reproducible build evidence #41616062998, actual Windows EXE + portable signing + real NSIS installer #41616063102. Trusted owner Windows QA #41616063011 was still **QUEUED**, not PASS. Always recheck after a later docs or feature merge.

## Work in progress: genuine official F-Droid repository import/network integration

[PR #62](https://github.com/rezamahrm100-ops/hamapp-store/pull/62), feature `feature/official-fdroid-real-test-repo-on-emulator-20261103`, includes a **separate, genuine upstream test** that builds actual debug APK v1 and v2 and two genuine `fdroidserver` signed indexes under one ephemeral key while ensuring private keystore/config are outside a separately served temporary repository HTTP webroot. It installs independently GPG+Android-signer-verified actual official F-Droid APK on hosted Android 33, sends a real `fdroidrepo://10.0.2.2:8975/...fingerprint=...` intent, attempts only accessibility-grounded UI confirmations, and requires **real Android client's HTTP index requests**, separately for v1 and v2. All ephemeral keys/APKs removed; no false claim of persistent official-client repo subscription, in-client APK install/update or production HTTPS owner repo.
- Initial exact-head hosted CI/CodeQL/Trivy **SUCCESS**, but actual real F-Droid client network test [#41617301607](https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41617301607) **FAILED** during private JAR validation before emulator due missing upstream direct-library `jarsigner` setup. Added explicit `fdroidserver.common.config = common.read_config()` identical to previously accepted actual signed-index drill. **RECHECK newer actual CI head and logs before claiming acceptance.**
- If the real official app cannot fetch signed HTTP index or Android accessibility UI is unavailable, leave PR unmerged and explicitly record actual blocker. A green source test alone never establishes network/Android acceptance.

## Remaining genuine engineering and external approval gates

- **Full F-Droid lifecycle:** official app persisting signed repo in its own DB, fetching verified APK, real in-client v1 install and v2 upgrade, negative wrong repo signer/changed APK and actual package verification on isolated emulator. Production requires owner-approved *durable* signing key/offline backup, approved HTTPS origin, authentic publisher app signing and physical-device consent. Prior signed-index-only/direct-adb upgrade is NOT F-Droid-client upgrade.
- **Publisher portal:** HTTPS quarantine exists, but real developer identity proof, MFA, token rotation/revocation, tenant-admin accounts/permissions, encrypted storage ops, malicious abuse/rate controls, independently verified author source/CA/antivirus/permission review and signed release/revocation human approval still not shipped. No release/paid features activated.
- **Windows release:** production authentic Authenticode developer signer/CA, MSIX/WinGet publisher-verified mapping, actual distinct app version update and rollback and consented owner-device GUI/UAC. Test unsigned NSIS does not meet production distribution.
- **GitHub ruleset:** `main` branch remains `protected=false`, repository rulesets `[]`, issue [#31](https://github.com/rezamahrm100-ops/hamapp-store/issues/31) requires owner/admin GitHub ruleset; connector lacks admin writes. GitHub Actions successful checks are not branch protection.
- **Other:** owner self-hosted Windows QA QUEUED, no production physical-device acceptance; no approved app publisher or production public download links. Keep safeguards and explicit off-switch.

**END VERDICT: ENGINEERING PARTIAL / PRODUCTION NOT READY.** This ledger lists true tested source capabilities and independently pending real-world permissions. No secret or unapproved package may be released.

## Next-run instructions

Read `AGENTS.md`, `docs/ONE-RUN-TECHNICAL-CLOSURE.md`, root/docs `NEXT-EXECUTION.md`, this exact RUN8 ledger and **live** main SHA/jobs, open PRs. Resume PR #62 only from actual CI logs; don't duplicate accepted #59-61. Advance additional independently engineerable publisher-account and signed Windows/F-Droid installation lifecycle gaps, perform real hosted tests and merge only exact SHA-gated green checks. Keep admin, signer custody, real DNS/public hosting, financial services and device owner consent as actual external gates. Record next accurate ledger after integration; don't stop at a status report.
