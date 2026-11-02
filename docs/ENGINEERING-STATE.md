# HamApp engineering state — handoff checkpoint

Checkpoint recorded 2026-11-02. **Never treat this snapshot as current evidence**: verify GitHub main SHA, workflow runs, release assets and signing registry on every continuation.

## Source of truth
Repository: https://github.com/rezamahrm100-ops/hamapp-store
Actions: https://github.com/rezamahrm100-ops/hamapp-store/actions
Pull requests: https://github.com/rezamahrm100-ops/hamapp-store/pulls
Issues: https://github.com/rezamahrm100-ops/hamapp-store/issues

Last independently inspected main commit *before accelerator work*: 46563fd8a381f679bb1bd997918de718939df24a.
Historical successful owner QA: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41475888396.
Historical successful CI: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41475888298.
Historical successful CodeQL: https://github.com/rezamahrm100-ops/hamapp-store/actions/runs/41475888321.
These are historical evidence, not claims that new modifications passed.

## Feature acceptance (do not inflate)
- Implemented: PWA catalogue, GitHub Pages deployment, CI on hosted Linux/Windows, CodeQL, Dependabot, owner-only Windows QA; offline candidate verification and F-Droid staging adapter.
- Partial: signed APK / Windows publisher verification needs real approved fingerprints, SDK tools and real installable packages.
- Missing: production F-Droid signer workspace and signed repository; independent actual app install/update on devices; branded Android client; Windows installer/update client; publisher portal, accounts/permissions and payment features.
- Publisher registry is deliberately empty: catalog/trusted_signers.json. Do not fabricate registrations or release links.
- New workflow generates provenance for PWA static bundle only, not an APK or proprietary application.

## Inspection commands
    gh repo view rezamahrm100-ops/hamapp-store
    gh api repos/rezamahrm100-ops/hamapp-store/commits/main --jq .sha
    gh run list -R rezamahrm100-ops/hamapp-store --limit 15
    gh pr list -R rezamahrm100-ops/hamapp-store
    gh issue list -R rezamahrm100-ops/hamapp-store
    python -m unittest discover -s tests -v
    python scripts/build_site.py
    python scripts/build_evidence.py --output dist/evidence

## Run/resource policy
Use hosted Linux and Windows for all untrusted PR code; no secrets in those jobs. Owner Windows runner label: hamapp-windows; execute trusted main only. Runner availability is dynamic; inspect each dispatched run, never assume online. Use public-hosted jobs for routine CI even if owner PC is off. Keep build artifacts short retention. Avoid caching dependency-free Python builds (no speed benefit). Protect main with required checks if repository admin capability becomes available.

## Release integrity guardrail
The SHA256 candidate gate and publisher gate check data and signing identity under explicit trust assumptions. A declared Git commit is not provenance, a hash receipt is not a signature, a GitHub PWA attestation is not an APK certificate, and F-Droid staging is not a signed published index. Actual marketplace release requires independent signing keys, device acceptance and permission review.

## Next work
Proceed through docs/NEXT-EXECUTION.md as a coherent end-to-end batch. Update this checkpoint after each accepted milestone with precise SHA and links.
