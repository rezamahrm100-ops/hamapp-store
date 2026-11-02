# Hosted source vulnerability/config/secret scanner and source SBOM

On each PR and trusted-main push, `.github/workflows/security-supply-chain.yml` checks out **public HamApp source** using GitHub-hosted Ubuntu, runs upstream [Trivy](https://github.com/aquasecurity/trivy-action) pinned to commit `ed142fd0673e97e23eac54620cfb913e5ce36c25` (signed v0.36.0 release), fails on actionable high/critical vulnerability, secret and misconfiguration results, and emits a CycloneDX SBOM with a short-lived GitHub Actions artifact.

No private application binaries, signing keys or user machine inventory are attached. Trivy uses public vulnerability databases downloaded within the hosted run. A DB outage or scanner failure must not be silently interpreted as no findings: this workflow is fail-closed. High/critical threshold is source CI policy; lower-severity findings are not a clean audit.

**Important:** A source filesystem scan and SBOM are NOT a malware verdict for a real APK or Windows EXE, independent Authenticode verification, license clearance, dynamic sandbox analysis, privacy/permission assessment or owner promotion approval. Binary-level Trivy package scans and OS permission/dynamic behavior review require a genuine publisher-approved artifact in a separate controlled analysis workspace. Public app registries remain empty/null.

Review exact Actions job SHA/run/summary and artifacts. No 'scan passed' claim based solely on this documentation. Trivy CLI is reused rather than implementing a bespoke vulnerability database or fictional malware scanner.
