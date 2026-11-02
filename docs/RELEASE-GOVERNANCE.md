# Owner-reviewed release governance: proposed revocation and admission

`scripts/release_governance.py` prepares a **review-only two-file patch** for catalog and release history. It never commits, changes the repo trust registry, deploys Pages, or authorizes publication. Public GitHub actions never receive production signer keys or private application binaries.

## Emergency revoke one approved binary

```bash
python scripts/release_governance.py --revoke-app <approved-app-id> --platform android --version 1.2.3 --artifact-sha256 <approved-64-char-digest> --output-dir /secure/review/revoke-001
```

The tool requires that the existing catalogue, signer registry and release ledger validate and the exact requested immutable identity belongs to a uniquely approved record. The proposed history changes the record to `revoked`; if the current public listing matches, its version, URL, release proof and changelog are removed and status returns to `planned`. It validates both proposed files **together**. The separate audit captures SHA256 of canonical before/after JSON and expressly sets `files_committed=false`, `site_deployed=false`, `github_owner_review_required=true`.

## Emergency revoke an entire publisher signer

```bash
python scripts/release_governance.py --revoke-signer <approved-certificate-sha256> --output-dir /secure/review/revoke-signer-001
```

Marks the certificate revoked, invalidates all its historical releases and removes any currently exposed matching downloads. Rejects unknown/previously revoked certificates. For real deployment the proposed `apps.json` and `release_history.json` must be reviewed, tested and merged in **one atomic Git tree/PR commit**, with owner approval, branch ruleset, exact latest main SHA and a verified Pages purge/rollout. NEVER update these files in separate public commits or bypass a review because it is an emergency. Strong branch protection is still an external admin-side blocker (Issue #31).

## Candidate admission

`release_governance.plan_promotion()` invokes the existing `integrated_release_review.assess()` in the trusted owner's separate controlled environment. That component invokes real OS APK/Authenticode verification plus upstream signed GitHub attestation, with publisher identity pinned in an independently reviewed registry. The planner produces a **proposal** only, always with `public_distribution_authorized=false`, `malware_permission_review_complete=false`, `signed_repository_and_device_qa_complete=false`, and no catalogue changes. Static boolean flags, uploaded JSON receipts, CI green or owner PR comments cannot alone authorize a production release.

Before production approval, obtain genuine signed artifacts and source attestations, independent vulnerability/malware/permission review of the exact immutable bytes, real F-Droid or Windows installation/update continuity, stable signer custody, and owner GitHub PR review with enforced branch ruleset. No real signers/releases exist in public registries at this checkpoint.

## Actual acceptance scope

Hosted Linux and Windows unittest jobs exercise revocation plan and negative cases with **synthetic** fixture identities; the source Trivy workflow scans **public source only**, not APK/EXE files. No real production rollback/revocation has been performed. Verify real GitHub Actions results before upgrading engineering status.
