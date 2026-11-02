# Integrated technical closure checkpoint — 2026-11-02

This document is a working gap-and-evidence matrix, not a statement that HamApp is complete. Live Actions and the actual merged SHA supersede this snapshot.

| Workstream | Implemented in this tranche | Acceptance | Remaining genuine gaps |
| --- | --- | --- | --- |
| Public PWA/offline | Deterministic planned-only offline snapshot in static build; Service Worker precache and no caching of live release catalogue; fallback UI cannot advertise downloads; JS syntax check | Hosted Linux+Windows CI, static build, negative source tests | Real browser accessibility audit, content/detail/changelog UX, privacy/permission review |
| Windows app operations | Commands run with interactive WinGet in a background thread; return-code is observed; GUI avoids false success or blocking main event loop | Hosted Windows unit tests and unsigned EXE build | Real independently authenticated package mapping, installed-version read-back, signed installer and owner-device install/update |
| Source provenance | Actual `gh attestation verify` invocation pinned to repo/workflow/source-ref/SHA, checks exact local artifact hash and SLSA subject; no injected JSON file is trusted | Synthetic negative control tests + actual gh CLI required when approved real candidate exists | Official owner-approved producer workflow/ref, authentic signed package, real gh verification, malware/permission review |
| Release review | Coordinates existing OS package signature/hash/version continuity and new verified producer attestation; refuses mismatches and never edits catalogue | Unit rejection matrix in CI | Owner-approved PR promotion transaction, real signing keys, approval ruleset and audit |
| Android client | Existing native debug app, F-Droid signed-index drill, v1→v2 update and downgrade/wrong-signer/corruption checks | Previously accepted Android 35 emulator runs | True owner-approved signed index and F-Droid client subscription/install/upgrades with stable repo key |
| Security/automation | Existing CodeQL, artifact attestations, self-hosted trusted-main runner; this tranche adds JS parser checks | Hosted checks | Branch ruleset Issue #31, full SBOM and malware scanner, private source intake |
| Production acceptance | No production trust roots or approved package links are introduced | Fail-closed empty registries | Genuine publisher approval, F-Droid durable offline backup, signed APK/Authenticode, physical-device QA and deployment approvals |
| Multi-publisher/commercial | No change: not a feature completed in this tranche | Not run | Authenticated publisher portal, tenant isolation, moderation, payments and external service readiness |

## Execution discipline

All production signer registries and real web origins remain empty. Synthetic tests confirm **rejection logic** only; source attestations and signature acceptance require real external evidence. No owner desktop or signing material is accessed by PR workflows. The production storefront remains a static demonstrator.

At the next run, first examine the exact integration-branch and main action results, then address the remaining engineering scope in priority order (real Windows installed-state verifier, editor/reviewer promotion pipeline, native Android F-Droid client acceptance, browser/a11y tests, production isolation design). Do not describe this matrix itself as an engineering completion result.
