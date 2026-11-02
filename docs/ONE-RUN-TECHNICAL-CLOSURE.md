# HamApp — ONE-RUN FULL TECHNICAL CLOSURE CONTRACT

Status: **binding priority for the next engineering execution**, effective 2026-11-02.
Supersedes any older handoff instructions that encourage advancing only one small defect, adding another paper-only gate, or ending after a status report. It does **not** supersede safety, owner permissions, verified release evidence or rules on self-hosted runners.

## Non-negotiable objective

**Finish and verify every technically actionable unfinished item across HamApp in the next integrated execution to the greatest extent that tools, time, runner capacity and approved permissions actually allow.**

The deliverable is a functional, cohesive, integrated application system and evidence-backed acceptance, not a list of suggestions or a series of tiny PRs separated by requests to the owner to say "continue". First do the work; only then report real outcomes. When different workstreams require separate security reviews or independent PRs, implement and integrate them **within the same execution**; do not interpret "one run" as "one enormous unreviewable commit". Never claim work was performed asynchronously.

A green demo, green unit tests, documentation, a fabricated fixture, a mock verification, or a test debug APK is **not** production acceptance.

## Required opening (read-only fact gathering, then implement)

1. Read root AGENTS.md, root NEXT-EXECUTION.md, docs/NEXT-EXECUTION.md, docs/ENGINEERING-STATE.md, docs/ROADMAP.md, docs/SECURITY.md, docs/GITHUB-ACCELERATION.md and this contract.
2. Inspect actual current main SHA, trees/files, open PRs (#4/#5/#6 if still open), issues (#1/#2/#3/#31 if still open), workflows/runs, jobs, artifacts, protected-branch status, GitHub permissions, and owner self-hosted runner trust model. Do not blindly merge dependency upgrades.
3. Build a machine-checkable **whole-project gap matrix** from the roadmap and source: module, desired behavior, present implementation, verification evidence, exact dependency/blocker, priority, owner, and acceptance test. Treat the matrix as a working plan, not the completed deliverable.
4. Group dependent workstreams for an integrated build and run them together where safe. Identify independent parallel hosted CI/jobs and shared upsteam components, avoiding redundant reimplementation.

## Whole-project workstreams to close — not isolated microfixes

### A. Foundation and operational reliability
- Audit Python build/validation, security and secret hygiene, dependency versions, licenses and action pinning; address actual defects.
- Establish safe PR/main checks, CodeQL, supply-chain/dependency review, reproducible artifact builds, checksums/attestations, deterministic test fixtures, diagnostic logs and fail-closed release policy. If the connected GitHub tools cannot create a branch ruleset, log a precise owner/admin-only blocker and continue other work.
- Reuse official GitHub-hosted Linux/Windows runners for PR code and the owner self-hosted Windows runner **only for trusted main**, never for unreviewed PR heads, untrusted PR artifacts or arbitrary external executables.
- Prepare a single reproducible integration/verification command or orchestration workflow where technically feasible; use existing workflows and upstream tools first.

### B. Android client and signed repository
- Complete native branded RTL UI, real metadata/detail/provenance/changelog UX, accessibility, resilience, safe approved F-Droid handoff and app lifecycle behavior; use pinned upstream F-Droid/fdroidserver components with license and trademark compliance.
- Implement full secure source-to-release ingestion and package/version/signer continuity using actual official APK tools and authentic build provenance; test updates, key mismatch, tampering, rollback, offline recovery and failure paths on an **isolated emulator**.
- Finish reusable tooling for persistent **owner-controlled** signed F-Droid index creation, backup/restore verification, signed-index subscription and staged release, without creating/storing real owner signing keys on public CI. Use disposable CI keys only for meaningful end-to-end engineering tests and label them non-production.
- Produce reproducible debug/unsigned test builds and evidence. Production developer APK signing, persistent repository key custody, independently pinned live HTTPS origin and physical-device confirmation remain owner/real-world acceptance gates if genuine identities or permissions are not available.

### C. Windows client and software management
- Complete native GUI/installer/updater engineering using official winget/MSIX/Authenticode primitives, explicit user consent and elevation prompts, pinned publisher/package identities, version continuity, anti-downgrade, uninstall/recovery, robust errors and accessibility.
- Exercise package-management operations against safe isolated or clearly approved fixtures; validate actual EXE packaging and GUI behavior on hosted Windows and additional approved, trusted-main owner runner checks where feasible.
- Implement and test owner-controlled signing/verification workflows **without** publishing credentials. Real production Authenticode certificates, package approval and interactive system modifications must not be fabricated or silently run.

### D. Storefront and publishing system
- Finish responsive RTL PWA: details/screenshots when verified assets exist, filters/search, release notes/changelogs, transparent download origin/provenance states, keyboard/screen-reader accessibility, offline behavior, correct caching/error paths, and no phantom statistics or downloads.
- Complete secure publisher submission/review/promote/revoke flows, authenticated service design only where actually needed, audit trail and atomic release promotion, trust registry, private metadata boundaries and rollback; use GitHub PR governance first where suitable, with a minimal backend only for demonstrated requirements.
- Verify exact web HTTPS origin, redirects and deployed immutable content where live approved evidence exists; keep all unapproved app launch/download controls disabled. Plan commercial infrastructure separately rather than silently turning Pages into a paid marketplace.
- Integrate source provenance + publisher certificate identity + binary digest + malware/permission policy + signed metadata + approved release history into one end-to-end fail-closed acceptance pipeline.

### E. Integration and definitive testing
- Run source tests, hosted Linux/Windows, CodeQL, Android emulator, Windows application/update tests, negative signature/corruption/revocation/downgrade tests, reproducibility/integrity and real provenance verifications. Investigate and fix failures, rerun until checks are green or a concrete blocking dependency is proved.
- Verify the exact branch and SHA for every conclusion, archive safe bounded artifacts and reports, keep test keys/binaries/private data out of public logs and assets, and verify post-merge checks on main.
- Do not substitute dozens of mocked receipts for genuine integrations. Preserve a stable security model even when test success would be easier by relaxing checks.

## Execution and merge policy

- **Do not stop after finding the first defect**, after building one small feature, after writing a plan, or after one green workflow. Move directly to the next dependent task while tools and permissions allow.
- Use a coherent engineering batch, with as many separable PRs as security and review require. Minimize chat/user turn overhead; never request "بریم" between automatically executable steps.
- For each PR: review diff, validate data and toolchain, run relevant hosted CI/CodeQL/actual integration tests; merge on demonstrated green checks with an expected head SHA, then validate main. Never force merge, disable security to get green, or call queued/in-progress checks complete.
- Prefer free GitHub facilities, the existing safe Windows runner, standard open-source maintained tools and reproducible pinned dependencies; do not incur unexpected costs or consume private secrets.
- Maintain a single current gap/acceptance ledger so the next session knows the precise remaining work without replaying completed stages.

## Separate technical responsibility from genuine external/owner gates

Assistant + authorized tools own: coding, reviewable architecture, build pipelines, automated CI and emulator tests, documentation, safe configuration generation, dry runs, and integration checks that need no additional real-world approval.

Owner-only or independent-real-world gates: actual signing-key custody and offline backups, purchase/issuance/approval of production certificates, approval to publicize private products, consent for interactive physical-device installation/UAC/system modifications, independently approved trust fingerprints/origins, enabling production releases, paid services, or elevated GitHub administration not exposed by current connectors.

**Do not mislabel an owner gate as unfinished coding.** Finish the code, test harness, documented commands and acceptance tooling for it as far as possible, then report the precise one-time owner action, minimal input and required post-action verification. Do not invent signatures, credentials, approval, fingerprints, source repositories, results or file access.

## Final result: mandatory evidence and honest exit conditions

At end, report in repository and user response:

1. Exact main SHA, PRs merged and changed subsystems with links.
2. Test matrix: successful, failed, not run, blocked — with exact workflow IDs and artifact/receipt references.
3. Engineering closure verdict: **PASS** only if all technically actionable scope is implemented and independently verified; **PARTIAL** if unfinished engineering remains, named explicitly; never conflate product-wide completion with preview acceptance.
4. Separate external/owner gates with rationale and minimal owner actions. No production release claim before real signing, independent trust, device and publisher approval.
5. Current next-execution contract and gap ledger in AGENTS.md, root NEXT-EXECUTION.md, docs/NEXT-EXECUTION.md and docs/ENGINEERING-STATE.md.

If environment/tool/time limits prevent finishing everything in that single execution, close as much as possible **now** rather than ending with a plan only. Be precise about incomplete items; avoid circular micro-work and superficial status updates.

## Compact instruction to future assistants

> Continue HamApp from live GitHub according to AGENTS.md and docs/ONE-RUN-TECHNICAL-CLOSURE.md. The objective is whole-project technical closure in one integrated execution—not a small fix or status report. Implement, test, fix and merge every feasible engineering workstream; reserve only genuine owner/external gates and commit the exact evidence/remaining gaps.
