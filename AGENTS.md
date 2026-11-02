# HamApp — canonical agent handoff

**Read this file first in every new chat, coding-agent session or runner task.**

Repository: https://github.com/rezamahrm100-ops/hamapp-store
Website (public static demo): https://rezamahrm100-ops.github.io/hamapp-store/
Owner: rezamahrm100-ops
Default branch: main

## What exists
- Persian RTL installable PWA catalogue (web/index.html, web/app.js, web/styles.css, catalog/apps.json).
- Python-stdlib site builder, catalogue validation and tests.
- Offline hash/size candidate gate (scripts/release_integrity.py).
- Offline publisher/signature gate and F-Droid staging bridge (scripts/publisher_gate.py, scripts/fdroid_bridge.py).
- GitHub-hosted Linux/Windows CI, CodeQL, Dependabot, Pages, and a separately registered owner Windows runner (hamapp-windows).
- Release evidence workflow and reproducible PWA ZIP (after this change is merged).

## Not completed / not authorized to claim
- No approved Android/Windows publisher identities: catalog/trusted_signers.json is empty.
- No real signed production F-Droid repository or offline key backup.
- No branded native Android client or Windows installer/updater.
- No independent two-version real-device install/update acceptance.
- No multi-publisher portal, paid marketplace or production account service.
- All public catalogue entries are planned; none have an approved download link.
- A green CI or an attested PWA ZIP does NOT mean a signed app or live marketplace.

## Read before making changes
1. docs/ENGINEERING-STATE.md (status + precise verification commands).
2. docs/GITHUB-ACCELERATION.md (existing/free tooling and cost/security limits).
3. docs/OPEN-SOURCE-REUSE.md (upstream reuse / licensing decisions).
4. docs/NEXT-EXECUTION.md (one coherent next engineering batch).
5. docs/SECURITY.md, docs/PUBLISHER-PIPELINE.md, docs/ROADMAP.md.

## Fast execution contract
- Inspect live main SHA, open PRs and latest check runs from GitHub. Documents are handoff context, NOT proof of today's runtime status.
- Prefer existing mature open-source tools, fork or vendor only when licensing/security and maintenance permit; pin versions and provenance.
- Implement one cohesive PR per independent tranche; run Linux + hosted Windows + CodeQL, investigate failures, then merge only green/reviewed code.
- User explicitly prefers GitHub/runner automation and no piecemeal local UI work. Do not request manual steps for tasks executable with authorized connectors and runners.
- Self-hosted Windows runner is for owner-trusted main only. Never run PR head, untrusted contributors, downloaded arbitrary code, or private secrets through public PR workflows.
- No owner signing keys in GitHub; no private source or user data copied into this public repository.
- Use immutable release identifiers, signer continuity, SHA256 and version-code checks; never turn on download links from synthetic fixtures.
- Never claim a change, workflow run, merge, installation or release succeeded without a real SHA/run URL/evidence.
- Keep this file and ENGINEERING-STATE.md updated when architecture or acceptance status changes.

## Local commands
    python -m unittest discover -s tests -v
    python scripts/build_site.py
    python scripts/build_evidence.py --output dist/evidence

Windows owner QA: .github/workflows/windows-qa.yml (main-only); ordinary CI: .github/workflows/ci.yml.
For a new chat: "Open AGENTS.md and docs/NEXT-EXECUTION.md at the current main SHA, inspect live checks, then continue the entire safe engineering batch via PR."

## Release continuity policy (added 2026-11-02)
- Read docs/RELEASE-HISTORY.md before release work. New release_history.py and release_review.py provide fail-closed pre-publish rollback/replay/revocation checks, not production authorization.
- catalog/release_history.json is initially empty; do not fabricate approved history or signer fingerprints. F-Droid offline staging now checks this ledger before accepting candidates.

## Public download admission rule
- Before enabling `released` in public catalog/apps.json read docs/CATALOG-RELEASE-GATE.md. HTTPS alone is NEVER evidence of signed software. Production binary listings must match approved history and independently registered publisher, while actual signing/provenance/device gates are separate.

## Accepted V1 release metadata hardening
- See docs/RELEASE-HISTORY.md and docs/CATALOG-RELEASE-GATE.md: review-only historical anti-rollback checks and approved-download gating. Historical PRs #12 and #13 merged 2026-11-02; their exact verified workflow evidence and outstanding gaps live in docs/ENGINEERING-STATE.md.
- Never mistake this for completed production F-Droid signing or native Android/Windows clients.

## Native Windows desktop preview (2026-11-02 implementation)
- Read docs/WINDOWS-CLIENT.md. The project includes a Python Tkinter/official winget client with owner-curated mapping, strict version/package IDs, explicit user confirmation and hosted Windows PyInstaller build.
- It is **unsigned**, not production release. All package mappings are empty, so no app installs are enabled. Check actual Windows preview workflow result before claiming EXE created.
- No unattended WinGet actions on the owner runner; client UI and signing identity require separate real-device and owner approval.

## Native Windows preview accepted (2026-11-02)
- PR #15 on main `d420ee6a3a93ec15bad9fec09154c4e5e2f46742`: actual GitHub-hosted Windows PyInstaller unsigned preview EXE built, Linux+Windows CI, CodeQL, self-hosted owner Windows QA, Pages and PWA evidence all passed. See docs/ENGINEERING-STATE.md for immutable run links.
- Read docs/WINDOWS-CLIENT.md before modifying Windows client. No real packages approved and no signed production desktop EXE; the GUI is a prototype with installation disabled until owner-curated mapping exists.
- Next focus: upstream-based Android client and true release signing/provenance. Never request owner desktop input when hosted runners can complete a trusted engineering check.

## Android native preview tranche (2026-11-02)
- Read docs/ANDROID-CLIENT.md, scripts/build_android_catalog.py and .github/workflows/android-client-preview.yml. Adds Android Java RTL offline catalogue; reuses separately installed upstream F-Droid through a verified-origin ACTION_VIEW handoff, **not** by forking or embedding F-Droid's GPL installer code.
- New Android workflow must pass genuine Gradle compile and artifact checks before claiming success. Debug key is ephemeral; never treat it as a production signing identity.
- catalog/android_repository.json is null; no independent verified F-Droid signing key/index or approved Android packages exist; all install buttons remain disabled.

## Hosted Android emulator QA (pending check)
- Workflow `.github/workflows/android-emulator-smoke.yml` provisions an isolated GitHub-hosted Android emulator, launches the native activity and verifies accessibility nodes show F-Droid installation disabled. This is **not** physical-device install/update acceptance. Check actual CI run before claiming success.

## Native Android + hosted emulator accepted (2026-11-02)
- Feature PR #17 merged at `4688fb18294a1e05ec3f3cf357c6a456a84009fb`. Hosted Android Gradle CI built and verified a debug-key APK. PR build: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41487326775 ; main build: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41487682003. Both succeeded.
- Emulator PR #18 merged at `56fe430abab33d4c4a843296778ed39c480e860e`. Hosted Android UI smoke succeeded: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41488084733 ; captures UI hierarchy and screenshot and proves F-Droid button disabled.
- Next check latest main CI and emulator rerun. The preview APK is debug signed, not production. No trusted F-Droid repo or accepted third-party APK exists. Never equate emulator smoke success with signed repo installation/update or real device QA.
