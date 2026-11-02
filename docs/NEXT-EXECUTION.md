# HamApp — next integrated execution contract

**Start from AGENTS.md and ENGINEERING-STATE.md. Verify live main, workflows, open PRs and issues.** Do not substitute this text for current GitHub data.

## Mission: finish as much independent engineering as possible in a cohesive run

### Tranche A: source identity and publication provenance (highest priority)
1. Inventory existing authorized source repositories and their verified release assets privately, without exposing private names/files in this public repo.
2. Build a machine-checkable allowlist of official source repo IDs, immutable release tags, exact asset digests and expected publisher cert identities. Do not register any signer from an untrusted APK or invented data.
3. Extend existing offline publisher gate with independently verified GitHub attestation check (gh attestation verify), source SHA identity and malware/permission scan. No claims based only on a source_sha string or fabricated receipt.
4. Create a protected owner-reviewed release promotion transaction: verified signed files, signed metadata, atomic catalogue update, revoked release rollback handling, auditable approval. Public download buttons must remain disabled until all gates pass.
5. Implement separately trusted WEB deployment origin approval before enabling `status: released` for `web` apps.

### Tranche B: native distribution (reuse upstream, do not build package tools from scratch)
1. Evaluate pinned F-Droid upstream client revision/build, license and trademark compliance. Prepare and test a properly branded Android client that can subscribe to a trusted signed repository. Android installation must honor OS prompts.
2. Integrate fdroidserver in an isolated private signer environment with persistent repo signing keys, independent backups, index verification, and public HTTPS publishing only after approved release evidence.
3. Use Windows Package Manager / winget / MSIX / Authenticode where applicable for a native Windows catalogue/install/update assistant, with explicit user approval for privileged operations and anti-downgrade rules.
4. Run Linux/Windows hosted checks first; self-hosted Windows runner only for code from trusted main. Use emulator/isolated devices for update continuity.

### Tranche C: front end, publisher workflow and acceptance
1. Reuse tested open-source UI components where licensed and beneficial, but keep RTL performance and accessibility. Build app details, changelog, provenance badges and verified link disclosure, without invented downloads or popularity statistics.
2. Start publisher operation via GitHub PR-based review and minimal audit logs; add backend/accounts only for actual access control needs. Do not put private publisher/source information in public JSON.
3. Test signed two-version Android and Windows installs, incorrect certificate, corruption, compromised/revoked signer, downgrade, offline restoration and failure recovery. Preserve signed index and trust root continuity.
4. Keep one cohesive, reviewable PR per independent release/installation workstream. Gate on hosted Linux + hosted Windows + CodeQL and inspect actual published artifacts. Production release needs genuine device and signer acceptance.

## Execution discipline
- Prefer GitHub Free public Actions, hosted runners, short-lived artifacts, attestation verification, standard package tools, maintained open-source upstream code, explicit pinned versions and licenses.
- Never run unreviewed PR code on owner Windows. Never upload private signing keys or unreviewed app binaries to this public repo.
- Update AGENTS.md and ENGINEERING-STATE.md after the batch with immutable SHAs/run links, exact acceptance gates and blockers.
- Avoid requesting manual tasks unless an unavoidable owner signing/authorization/device gate remains. Do not announce completion without actual evidence.
