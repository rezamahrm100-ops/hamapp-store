# HamApp — integrated engineering RUN9, 2026-11-03

**Engineering PARTIAL; production NOT APPROVED.** Evidence must be checked against live GitHub; this is not a release authorization.

## Three genuine source merges accepted

**PR [#64](https://github.com/rezamahrm100-ops/hamapp-store/pull/64)** merged SHA `69cffd6753a8391ac5d9dcfdea5eccf30c172503`. Adds owner-private atomic bearer-token add/rotate/revoke under POSIX filesystem lock, 0600 credential registry, independent fsync, with immediate running-local-HTTP and running-real-HTTPS enforcement. Old/revoked tenant tokens are rejected on next submission. Real TLS, file-quarantine and negative tests passed, with feature CI [#41620746642](https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41620746642), CodeQL #41620746711 and Trivy #41620746626 all **SUCCESS**. This is not legal developer identity, MFA, public account hosting or release approval. See [publisher token lifecycle](PUBLISHER-TOKEN-LIVE-REVOCATION.md).

**PR [#62](https://github.com/rezamahrm100-ops/hamapp-store/pull/62)** merged SHA `9c2c14ba1b5270657ff0ac9250dcdb3e45233dfc`. Built two actual different Android debug APKs and two authentic signed F-Droid indexes under one disposable repository signer; official downloaded F-Droid Android APK independently GPG+developer-certificate verified; private disposable HTTPS/ephemeral CA configured on disposable Android 33 emulator, and **real official F-Droid client HTTP requests for signed index v1 and then v2** were actually observed. Real hosted Android [#41622191773](https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41622191773), CI #41622191798, CodeQL #41622191720, Trivy #41622191759 **SUCCESS**. Only bounded screenshot/receipt retained, no private key. **Not proven**: native client DB persistence, in-client APK install/update, production HTTPS origin, owner key/device. See [real upstream test](FDROID-OFFICIAL-CLIENT-REAL-SIGNED-REPO-LAB.md).

**PR [#65](https://github.com/rezamahrm100-ops/hamapp-store/pull/65)** merged SHA `e8bb47027087d63bd0f9cb467011b393dbd7a98b`. On hosted Windows Server 2022, compiled **two actual different native GUI PyInstaller EXEs** using distinct source build labels and digests, installed v1 using actual unsigned NSIS per-user installer, installed distinctly compiled v2 via real installer upgrade and verified actual v2 file hash, refused older downgrade preserving v2 and performed actual uninstaller/disk/HKCU cleanup. Real [Windows NSIS integration #41623081767](https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41623081767), CI #41623081780, CodeQL #41623081783, Trivy #41623081697 **SUCCESS**. Test binaries stay in disposable CI; no production Authenticode CA, SmartScreen, WinGet or physical device acceptance. See [Windows QA](WINDOWS-NSIS-INSTALLER-REAL-QA.md).

## Integrated main evidence

On exact main `e8bb47027087d63bd0f9cb467011b393dbd7a98b`, six hosted runs **SUCCESS**: [CI #41623437298](https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41623437298), CodeQL #41623437324, Trivy #41623437342, real Windows EXE+portable cryptography+NSIS #41623437307, reproducible build #41623437205 and Pages #41623437265. Trusted owner self-hosted Windows QA #41623437229 **QUEUED, NOT PASS**. Main still `protected=false` and GitHub rulesets `[]`; admin-only [issue #31](https://github.com/rezamahrm100-ops/hamapp-store/issues/31) unresolved.

## Current dependent PR #66 — not accepted without Android DB proof

[PR #66](https://github.com/rezamahrm100-ops/hamapp-store/pull/66) adds **read-only true SQLite persistence verification** of actual official F-Droid client private database after v1/v2 signed index real requests on disposable emulator. Only a bounded non-secret receipt, no SQLite contents or keys, may be retained. Source tests are not equivalent to real Android DB acceptance. Verify exact PR head CI, CodeQL, Trivy and real emulator success; otherwise **leave unmerged**. Do not turn two network index GETs into an unverified installed repository claim. See [candidate scope](FDROID-OFFICIAL-REPO-SQLITE-PERSISTENCE.md).

## Outstanding engineering vs real-world owner gates

Real F-Droid client app v1 installation and v2 update FROM its own repo, saved signer pin verification, publisher account MFA/identity/tenant review, owner-controlled production release governance, Windows native trusted production Authenticode/installer/WinGet, physical device acceptance and admin branch protection remain open. Owner/external dependencies include authentic source/publisher identities, key/certificate issuance and offline custody, real HTTPS origin, approved first product, admin ruleset and consented owner-device acceptance. No production signer or first approved download exists; public package registry remains unapproved/empty.

## Next run

Read live GitHub SHA and checks, `AGENTS.md`, root/docs `NEXT-EXECUTION.md`, `docs/ONE-RUN-TECHNICAL-CLOSURE.md` and this ledger. Finish any genuine open PR #66 after real Android evidence, advance non-secret engineerable remaining work, verify exactly matching hosted security and integration workflows, merge only proven green, recheck main and update this ledger. Do not repeat already accepted #62/#64/#65 milestones or confuse a queued trusted Windows QA with a PASS.

**Verdict = PARTIAL, release NOT APPROVED.**
