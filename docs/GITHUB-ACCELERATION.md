# GitHub acceleration matrix — HamApp

Goal: maximize safe, verified engineering throughput on GitHub Free, while minimizing owner UI steps and avoiding invention of package-management engines.

## Already exercised and confirmed in this repository
- Public repository, branch-based development, PRs and merges.
- Actions on hosted Linux and Windows; owner-scoped self-hosted Windows QA (trusted main only).
- Pages website deployment with no purchased domain.
- CodeQL JavaScript/Python, Dependabot GH Actions update PRs.
- Issues (#1 F-Droid, #2 native clients, #3 publisher portal), scheduled CodeQL.
- Maintained Python zero-dependency build and tests.

## Now being enabled by the accelerator PR
- Root AGENTS.md and .github/copilot-instructions.md for durable chat/agent context.
- A reproducible site ZIP with SHA-256/size evidence, bounded retention as a workflow artifact.
- GitHub Actions artifact attestation for the **static storefront ZIP only**, never claimed as APK/Windows signature.
- A testable build-evidence Python command, local or GitHub-hosted.

## Strong next upgrades (not implemented until a verified run says so)
1. Require PR and passing Linux/Windows/CodeQL checks on main via branch ruleset (public GitHub Free supports rulesets; requires admin permission). Never disable protection for speed.
2. Signed tagged releases and authenticated source->build provenance for each real app via its own private release pipeline; retain immutable SHA, identity and SBOM.
3. Reusable workflows/shared composite actions when at least two owned repos genuinely share the same release contract; avoid premature abstractions.
4. GitHub Releases for versioned artifacts; artifact attestation and gh attestation verify; separate production binaries from short-lived CI artifacts.
5. Dependency Review on PR and Syft-generated SBOM/Trivy vulnerability scan after pinning maintained upstream actions; review licensing and action trust.
6. Optional GitHub Projects board only when it measurably reduces work; canonical acceptance stays in issue/PR + docs.
7. Release changelog generation via GitHub release notes and conventional commits.
8. Avoid Codespaces, GitHub Models or paid Copilot assumptions: features and free quotas vary by account/plan; do not silently incur charges.
9. Cache only expensive pinned dependencies (Android SDK, Gradle, etc.) with bounded keys, size limits and no secrets; current Python stdlib site has no useful dependency cache.
10. Android emulator on hosted Linux/Windows or separately isolated runner for signed APK install/update acceptance. Production signing keys remain on trusted controlled signing environment.

## Public site cost and terms
GitHub Pages hosts this public *static project showcase*. GitHub Pages terms prohibit using it as free hosting for an online business, e-commerce, or primarily commercial SaaS. If HamApp later sells software or becomes a commercial marketplace, migrate public production hosting to appropriate infrastructure. Do not use GitHub Releases as an unlimited binary CDN.

## Security and approval
Never give public PR authors access to self-hosted machines or any sensitive action secrets. Keep workflow permissions minimal and release signing keys off GitHub. Avoid automatic merging of Dependabot PRs without checking breaking changes. GitHub Actions on standard hosted runners in public repos and self-hosted executions are free from GitHub compute billing, but have resource and usage limits.

## References
- GitHub Actions billing: https://docs.github.com/en/actions/concepts/billing-and-usage
- Artifact attestations: https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations
- Rulesets: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets
- Pages limits: https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits
- Copilot instructions: https://docs.github.com/en/copilot/reference/customization-cheat-sheet
