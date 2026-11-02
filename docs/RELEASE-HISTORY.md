# HamApp V1 — owner-reviewed release continuity and rollback protection

This project now contains a **prepublication continuity policy**, not an automatic app publisher.

## Trust boundaries
- `catalog/trusted_signers.json` pins independently approved developer signing certificate fingerprints. It is empty now; no genuine app is trusted.
- `catalog/release_history.json` records separately approved historical releases and revoked signer certificates. It is initially empty and must be reviewed through a protected branch/PR. This is an owner-approved policy ledger, NOT an immutable ledger, cryptographic signature, or verified GitHub attestation.
- `scripts/release_history.py` refuses version rollback/replay, artifact hash reuse, signing identity substitution, source repo/package-id substitution, revoked signing identity, and Android versionCode rollback. Revoked versions still participate in version floors.
- `scripts/release_review.py` first checks historical policy, then verifies candidate bytes and signing certificate through existing publisher_gate, and writes a **review-only** receipt. It never edits the ledger, uploads binaries, creates signing keys or publishes downloads.

## Usage
```
python scripts/release_history.py --candidate candidate.json --registry catalog/trusted_signers.json --history catalog/release_history.json
python scripts/release_review.py --candidate candidate.json --artifact signed.apk --receipt review.json
```

The second command is restricted to genuine signed Android or Windows artifacts with known publisher identities. Mocked tests do not approve applications. A proposed record includes `status: pending` and **cannot be pasted into approved history**, whose allowed statuses are `approved` or `revoked`; approval requires out-of-band reviewer validation and source provenance/attestation verification. Certificate rotation requires an explicit migration policy, not silent acceptance.

Do not expose receipt files containing private data in the public repository. Reject an untrusted pull request modifying history/trust root. History is a contract and additional guardrail, not a cryptographic security boundary if GitHub write permissions are compromised.

Production acceptance still requires a persistent offline F-Droid repo signing key, signed index verification, independent APK signature verification, Windows Authenticode, source provenance, malware policy, physical or isolated test device installs, and two-version update continuity. See [PUBLISHER-PIPELINE.md](PUBLISHER-PIPELINE.md) and [NEXT-EXECUTION.md](NEXT-EXECUTION.md).
