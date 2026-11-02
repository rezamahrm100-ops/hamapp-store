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
