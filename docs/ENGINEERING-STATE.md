# HamApp — engineering state and evidence ledger

Checkpoint: 2026-11-02. Always query live GitHub before trusting this snapshot.

Repository: https://github.com/rezamahrm100-ops/hamapp-store
Default branch: main; public code only, existing proprietary app repositories stay private.

## Last inspected feature commits
- PR #12: https://github.com/rezamahrm100-ops/hamapp-store/pull/12 — merged to main SHA `81effa33d2ace1c537a3de792816cf901d549272`. Release history/revoked certificate/anti-rollback precheck added to F-Droid staging; no live binary published.
- PR #13: https://github.com/rezamahrm100-ops/hamapp-store/pull/13 — merged to main SHA `8ca141f25fed22f053b1d2940ca47e97ebf1ead2`. Public binary downloads require matching approved historical release and pinned publisher. Existing catalogue remains entirely planned.
- PRIOR PR #11: `ba61a72d6383eacbde6310524b82b8ea536a32ca`; agent handoff, CI artifacts and PWA provenance.

## Confirmed check runs on PR #12
- PR CI Linux/Windows: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41479750814 — success.
- PR CodeQL: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41479750912 — success.
- After merge: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41479970518 — owner Windows QA success; plus CI, Pages, PWA evidence and CodeQL successful for that merged SHA.

## Confirmed checks on PR #13 before merge
- PR CI Linux/Windows: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41480594525 — success.
- PR CodeQL: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41480594353 — success.
- Main at `8ca141f2...` started runs:
  - CI: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41480826636
  - Owner Windows QA: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41480826520
  - Pages: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41480826697
  - Static PWA attestation: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41480826823
  - CodeQL: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41480826720
  These run IDs are immutable evidence links, but recheck their terminal status on every continuation.

## Implemented (engineering)
- Persian RTL static PWA with search/platform filters and planned catalogue.
- GitHub Pages, CI hosted Linux/Windows, CodeQL, Dependabot, owner-only trusted main Windows runner, artifact evidence/attestation for static PWA.
- Owner-pinned offline publisher verification via Android apksigner/aapt or Windows Authenticode; failure-closed when registry has no owner-approved signers.
- Offline fdroidserver staging adapter, no deployment/keys.
- `catalog/release_history.json` review-only history schema; pre-publish versionCode/SemVer monotonicity, replay, signer revocation, source/package/signature continuity.
- `scripts/release_review.py` offline plan; no automatic owner approval or publication.
- `scripts/validate_catalog.py` prevents unapproved binary download buttons by cross-checking trusted signer and newest approved history. CI/Pages builds fail on invalid records.
- CODEOWNERS assigns owner review responsibility; it does not enforce branch protection without a configured ruleset.

## NOT accepted: remaining production gates
- Real approved trusted publisher fingerprints (registry empty).
- Actual independent source-to-binary provenance and release signing attestations for each Android/Windows product.
- Persistent offline F-Droid repo signing key, backup, signed published index, trust fingerprint.
- Real signed APK / Authenticode installer validation against independently approved identities.
- Android native branded client, Windows native installer/updater, safe version migration, backend publisher portal.
- Real device install/update between two consecutive signed versions, malformed/rollback/recovery tests.
- Web release verified-deployment origin policy and privacy/permission review.
- Payment/multi-publisher commercial marketplace.
- No real installable package download listed: all entries remain planned.

## Commands for independent confirmation
    gh repo view rezamahrm100-ops/hamapp-store
    gh api repos/rezamahrm100-ops/hamapp-store/commits/main --jq .sha
    gh run list -R rezamahrm100-ops/hamapp-store --limit 20
    gh pr list -R rezamahrm100-ops/hamapp-store
    python -m unittest discover -s tests -v
    python scripts/build_site.py
    python scripts/build_evidence.py --output dist/evidence

## Safety
Self-hosted Windows only on reviewed main; no public PR head code. No secrets/keys in GitHub. GitHub PWA build attestation is not an APK signature. Approved history is user-controlled metadata, not itself cryptographic proof of a release. No fake publisher entries, URLs or signatures.

See NEXT-EXECUTION.md for next integrated work. After every merge record new SHA and complete workflow outcomes.

## New Windows native client preview tranche (2026-11-02)
- Added native Python Tkinter GUI, read-only validated embedded catalogue, bounded winget install/upgrade/show invocation, negative tests, and Windows-hosted PyInstaller build in `.github/workflows/windows-client-preview.yml`.
- All WinGet mappings remain empty: not yet able to install real apps. No signed EXE or owner real desktop UI acceptance.
- **This is an implementation checkpoint, not evidence that GitHub checks succeeded.** Inspect the live PR and action result before accepting.
