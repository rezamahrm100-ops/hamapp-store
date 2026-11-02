# Instructions for GitHub Copilot on HamApp

Read AGENTS.md at repository root and docs/ENGINEERING-STATE.md before editing. Live GitHub state overrides any dated checkpoint. Keep all explanations precise about tests, signatures and actual device acceptance.

Architecture: dependency-free Python stdlib tooling in scripts/, tests/ using unittest, RTL static PWA in web/, validated public metadata in catalog/, hosted CI in .github/workflows/. Prefer open-source upstream package ecosystems instead of recreating them. The public catalogue must not expose unverified download buttons or private publisher data.

Required workflow: inspect tests and trust boundaries, implement coherent change, run python -m unittest discover -s tests -v and python scripts/build_site.py, validate Linux + hosted Windows + CodeQL checks on PR, merge only after successful checks. Never place unreviewed PR code on self-hosted Windows. No signing private keys or credentials committed, displayed or uploaded. Distinguish a static build attestation from an APK/Authenticode signature. Update the handoff documents when status materially changes.
