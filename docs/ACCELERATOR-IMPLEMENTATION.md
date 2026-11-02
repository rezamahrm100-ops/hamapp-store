# Accelerator implementation verification

This PR introduces a new workflow for GitHub-hosted static-site artifacts. This provenance attests only the generated public PWA ZIP: it does not sign an Android package, Windows executable, or F-Droid index.

- AGENTS.md is the primary handoff file for future ChatGPT chats and coding agents.
- .github/copilot-instructions.md assists GitHub Copilot in supported contexts.
- ENGINEERING-STATE.md captures audited historical status but requires fresh checks every session.
- build_evidence.py makes a stable ZIP sorted by path with normalized timestamps and archive mode; machine-readable SHA-256 evidence and honest negative scope.
- build-evidence.yml runs only trusted main, uses minimal scoped permissions necessary for attestation, retains evidence artifacts seven days.
- Pull request template records test results and security acceptance.

Validate by observing a successful workflow on actual main SHA, not merely successful unit tests. If attestation fails because of GitHub policy/permissions, investigate from logs before claiming success.

Future work: enforce branch rulesets using administrator authorization, use release attestations and SBOM for true APK/Windows builds, reuse workflows across repos only after at least two independent adopters, then finish real-device installation and update acceptance.
