# HamApp integrated source engineering — 2026-11-03 RUN7

**Status: PARTIAL source engineering; production release NOT APPROVED.**
This ledger is a snapshot of **verified GitHub facts** at this run. Always re-read the live main SHA and workflow conclusions before claiming a new success. Never convert a queued trusted owner Windows check to a PASS.

## Closed actual engineering this run — PR #56

[PR #56](https://github.com/rezamahrm100-ops/hamapp-store/pull/56) was safely **merged** at main SHA `2cd503aa0247f73de960137ca45a4c85b21edf61`; exact final PR source head `ade1023699698e8bebc8e73d480b20290dfae94b`.

The working build/cryptographic acceptance path now uses **two independent GitHub-hosted jobs**, not native Windows CurrentUser trust-store calls:

1. `windows-2022` builds the actual PyInstaller Windows client `HamApp-Windows-Preview.exe`. The short-lived artifact **remains UNSIGNED**; source tests fail closed. This is a real Windows PE binary, not a pretend `.exe` fixture.
2. `ubuntu-24.04` takes the **exact artifact from the same GitHub run**, uses upstream `osslsigncode 2.8` and pinned `cryptography==50.0.2` to create TWO genuine disposable **root CA → code-signing leaf** chains, signs two copies of the actual EXE, and verifies the actual embedded Authenticode cryptographic signatures and exact SHA-256 of the signer leaf. Test negatives reject the unsigned EXE, the foreign genuinely signed EXE with the wrong pinned certificate, the wrong CA and a real modified byte in the signed executable. It re-verifies unchanged original EXE digest and destroys all ephemeral PFX/private passwords, signed EXEs and key files before upload.
3. Only a bounded, **non-secret receipt** is uploaded. The temporary signed test executables are NEVER published or offered for installation. Production catalog signer registries and download links remain EMPTY.

### Exact real evidence on immutable feature head

- [Actual Windows EXE + real portable Authenticode with all negative cases #41611354053](https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41611354053): **SUCCESS**. Jobs `desktop-preview` and `Real offline PE Authenticode with two disposable publishers` both **SUCCESS**.
- [CI Linux/Windows #41611354129](https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41611354129): **SUCCESS**.
- [CodeQL #41611354054](https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41611354054): **SUCCESS**.
- [Hosted supply-chain/Trivy #41611354138](https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41611354138): **SUCCESS**.
- [Short-lived safe artifact](https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41611354053): `hamapp-real-disposable-portable-authenticode-evidence`, ID `13218169972`, approximately 642 bytes ZIP; original **unsigned preview** artifact ID `13219231930`. These have normal expiry; never infer payload bytes from the names alone.

### What was genuinely broken, and what changed

Prior hosted native Windows attempts hung during `New-SelfSignedCertificate`, then during `.NET CertificateRequest.CreateSelfSigned`, then after a real PFX generation before the initial Windows SDK signing marker. They hit an eight-minute time limit; **none was a native Windows signing PASS**. Tests were moved to disposable GitHub-hosted Linux for real portable Authenticode. Subsequent Ubuntu `osslsigncode 2.8` initially rejected an unsupported newer `-ignore-crl` flag, then rejected the `sha2` alias when passed to OpenSSL's EVP name resolver. The final genuine test instead uses the supported `-ignore-cdp` option and OpenSSL `sha256` digest label; all actual positive and negative tests finished **SUCCESS**, not just static unit fixtures.

## Trusted-main status immediately after merge

Main became `2cd503aa0247f73de960137ca45a4c85b21edf61`. On the initial main recheck, CI #41611654912, CodeQL #41611654779, Trivy #41611654746, Pages #41611655148, native unsigned preview + portable signature #41611655045, reproducibility #41611654770 were **IN PROGRESS**; trusted self-hosted owner Windows QA #41611654981 was **QUEUED**. Do not mark these as success unless later live output confirms terminal SUCCESS. A subsequent documentation-only merge will create a new main SHA, requiring a fresh check of its own CI/CodeQL/Trivy.

## Strict acceptance boundary — do not misrepresent this test

**Verified now**: a real Windows PE executable built on official hosted Windows and genuine *cryptographically checked portable Authenticode* using disposable CI identities, including negative unsigned, different signer, wrong CA and PE-tamper checks. This is substantial source/security engineering closure.

**NOT verified**: native Windows `WinVerifyTrust`/`Get-AuthenticodeSignature` trust on Windows, trusted commercial code-signing CA, Windows SmartScreen reputation, MSIX installer signing, UAC installation, WinGet mapping against an actual approved app, owner Windows interactive QA, real production publisher identity, production release. Temporary self-signed test roots are not public developer certificates.

## Other independent whole-project gaps

- **Android/F-Droid**: previously accepted official upstream signed APK GPG+developer cert validation, actual official client installed on hosted Android 35 and real `fdroidrepos://` intent to official process (PR #55); prior two-version debug Android install and signed-index continuity also passed. **NOT DONE**: genuine official F-Droid client subscribing to trusted signed test repository, downloading a verified APK from it and installing/updating two real approved versions; native UIAutomator hierarchy was unavailable and recorded false. Production requires independently approved persistent offline repo signer, HTTPS origin, authentic app publisher and user consent.
- **Publishers/release governance**: private owner-local authenticated publisher quarantine exists. **NOT DONE**: full Internet-facing authenticated remote verified-developer identities, MFA, tenant isolation, operational encrypted storage, public-rate controls, moderation, genuine publisher signed release/promote/revoke approval and first eligible real product. No public binary links until all independent trust/provenance/malware/privacy checks pass.
- **Windows**: real production code signer/key custody, approved installer/MSIX and WinGet registration, consented install/update/rollback, physical owner QA still pending.
- **GitHub administration**: `main` is **not protected** in observed repository branch metadata. [Issue #31](https://github.com/rezamahrm100-ops/hamapp-store/issues/31) needs authorized owner-admin branch ruleset. Connected GitHub actions do not expose the required administration permission.
- **Owner trusted runner**: queueing is **not** acceptance. Hosted PR builds never run unreviewed code on the owner Windows runner.

## Next integrated execution

1. Re-read `AGENTS.md`, `docs/ONE-RUN-TECHNICAL-CLOSURE.md`, root/docs `NEXT-EXECUTION.md`, this exact ledger and live main/PRs/checks. **Do not repeat** genuine accepted PR #56 cryptographic PE work.
2. Prioritize actual disposable official F-Droid-client **signed repository subscription + two-version app install/update** on hosted Android, not only intent or `fdroidserver` index signing; retain physical/production gates.
3. Implement missing engineerable remote publisher/identity/tenant/review governance and Windows MSI/MSIX/WinGet validation tools with upstream components, as feasible. Any live production credentials, owner signing materials, public origin/device approvals remain separate owner-only gates.
4. Obtain authorized admin-only GitHub ruleset for protected main, check trusted owner Windows QA on exact main. Do not modify personal devices or expose real signing materials from PR code.
5. Run exact source Linux/Windows, CodeQL, supply-chain, real Android emulator, portable code-signing tests and trusted-main workflows when appropriate; merge only after their actual SUCCESS, then refresh this state for the following chat.

**Engineering verdict = PARTIAL; production release = NOT APPROVED.** This is an implementation/test ledger, not permission to turn on public downloads or claim the commercial marketplace has shipped.

## Verified terminal main recheck on 2cd503aa…
After the initial checkpoint above, **all SIX applicable GitHub-hosted main runs finished SUCCESS** on exact main SHA `2cd503aa0247f73de960137ca45a4c85b21edf61`: [CI #41611654912](https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41611654912), [CodeQL #41611654779](https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41611654779), [Trivy #41611654746](https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41611654746), [portable genuine signature + unsigned preview #41611655045](https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41611655045), [reproducibility #41611654770](https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41611654770), [Pages #41611655148](https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41611655148). Owner-only trusted Windows QA [#41611654981](https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41611654981) was still **QUEUED** and cannot be claimed SUCCESS.
