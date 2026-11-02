# HamApp — stable entry point for the next execution

**Canonical detailed task plan:** [docs/NEXT-EXECUTION.md](docs/NEXT-EXECUTION.md). This root file exists so new chats and coding agents can reliably find the handoff. It does not supersede the canonical detailed plan or live GitHub evidence.

## Mandatory order

1. Read [AGENTS.md](AGENTS.md), [docs/ENGINEERING-STATE.md](docs/ENGINEERING-STATE.md), [docs/NEXT-EXECUTION.md](docs/NEXT-EXECUTION.md), [docs/SECURITY.md](docs/SECURITY.md), and [docs/GITHUB-ACCELERATION.md](docs/GITHUB-ACCELERATION.md).
2. Fetch current `main` SHA, recent GitHub workflow runs, open PRs and issues; verify actual acceptance results. Never trust a dated markdown checkpoint as proof.
3. Continue the next complete, **safe** engineering tranche via a reviewable PR. Reuse upstream F-Droid, Android SDK, winget and native GitHub tooling rather than rewriting package managers.
4. Gate changes on hosted Linux/Windows CI, CodeQL and workflow-specific real Android/Windows integration tests. Self-hosted Windows QA is trusted `main` only, never arbitrary PR head.
5. Merge only green/reviewed code and record exact merge SHA, workflow URLs, remaining gaps and next actionable instruction in AGENTS.md / docs/ENGINEERING-STATE.md / docs/NEXT-EXECUTION.md.

## Latest verified engineering milestones (2026-11-02)

- PR #27: actual hosted Android 35 v1→v2 **debug** upgrade and downgrade denial, merged `df47991144c4a226fe76552cadbf351b1bc7c197`.
- PR #28: actual foreign-signer and truncated APK update denial, preserving installed debug v2, merged `1a5e43a4e59d1ce17966c83d6042eb78127fe681`.
- PR #29: offline immutable owner-reviewed web origin/release metadata gate, merged `eb08797a42fdde5cfacd0f6542ee0100d02bb680`. Registries deliberately remain empty. This is NOT a live deployment attestation.

## What is **not** completed

- No independently approved production publisher identities; no stable owner-controlled repo signing key with offline backup; no signed public F-Droid origin and client subscription; no production signed APK/Windows installer; no independent owner-device two-version install/update acceptance.
- No verified eligible private product promoted for public download; no production publisher portal, payments or multi-tenant marketplace. Do not fabricate approvals or convert ephemeral debug keys into trusted production signers.

**Next high-value gate:** independently register a genuine eligible release source, stable developer cert and owner-controlled F-Droid repository signing identity (outside this public repo), verify immutable source/release provenance and a signed production v2 index against an independently pinned fingerprint, then perform F-Droid client install/update and recovery on isolated Android before any public link is enabled.

## One-line instruction for future ChatGPT sessions

> پروژهٔ هَماپ را طبق AGENTS.md و NEXT-EXECUTION.md از آخرین وضعیت واقعی GitHub ادامه بده؛ همهٔ کارهای فنیِ امن و قابل‌اجرا را با GitHub و رانرها در یک ران یکپارچه پیاده‌سازی، آزمون و ادغام کن؛ نتیجه و دستور ادامه را در مخزن ثبت کن.

Repository: https://github.com/rezamahrm100-ops/hamapp-store
