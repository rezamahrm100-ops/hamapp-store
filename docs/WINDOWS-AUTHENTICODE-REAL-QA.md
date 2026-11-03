# HamApp — real Windows-hosted Authenticode EXE signing and rejection acceptance

## Engineering objective
The Windows preview previously produced a real **unsigned** PyInstaller EXE and only mocked signature/publisher verification on candidate packages. The hosted `windows-client-preview.yml` pipeline now produces the same real EXE, keeps it **UNSIGNED** as the short-lived preview artifact, and signs **two separate temporary copies** using different Windows CodeSigningCert certificates generated on **ephemeral GitHub-hosted Windows**. This is authentic Windows cryptographic signing, not a mocked PowerShell success flag.

The drill:
1. Invokes Windows `New-SelfSignedCertificate -Type CodeSigningCert` for signer A and unrelated signer B, with non-exportable disposable private keys. Temporary trust is limited to `Cert:\CurrentUser\Root` and `Cert:\CurrentUser\TrustedPublisher` on the isolated hosted runner.
2. Signs two actual preview EXE copies with Windows `Set-AuthenticodeSignature`, rechecks native `Get-AuthenticodeSignature` through the existing `scripts/publisher_gate.py`, and computes SHA-256 fingerprints of the actual signer DER certificates.
3. Constructs a **synthetic local-only, not-published** candidate and source registry and verifies the intended signer and precise EXE digest; rejects the unsigned original, the other *genuinely signed* EXE under the first publisher pin, and an EXE altered after signing.
4. Emits a bounded JSON receipt whose `public_release_authorized`, `production_authenticode_certificate_verified`, `trusted_prod_publisher_registered` and `windows_real_install_or_upgrade_verified` are explicitly **false**. Removes both ephemeral CI private keys/certificates from CurrentUser stores, deletes signed test EXEs and all temporary workspace bytes. Only an unsigned preview artifact and **receipt without keys or executable** are eligible for upload.

## Exact scope and trust limitations
- A **temporary self-signed certificate deliberately imported into the runner's CurrentUser trust store is NOT a real publisher/production Authenticode certificate**, public PKI identity, SmartScreen approval, hardware-backed signer or publisher registration.
- No private owner product, user secrets or persistent certificate is handled by public PR builds. The trusted owner Windows runner remains main-only and is not used for this drill.
- Windows GUI preview remains unsigned and not installable as production. No unreviewed WinGet package is mapped and real installer elevation/UAC/update/rollback never runs on the owner's machine.
- Source unit tests never substitute for Windows PowerShell and real signed EXE results; require successful actual hosted Windows run and saved evidence under `hamapp-real-ephemeral-windows-authenticode-evidence`.

## Review/acceptance
Run `python -m unittest discover -s tests -v` on Linux/Windows and inspect real `.github/workflows/windows-client-preview.yml` on exact PR SHA. The Windows preview job must succeed across signed-certificate verification, two actual distinct signatures, unsigned/wrong-signer/tamper rejection, unchanged original unsigned artifact and receipt upload; CI/CodeQL/Trivy must also be successful. Independently confirm after merging on main.

## Remaining real-world gates
Owner-approved developer certificate SHA256, hardware/secure signing key custody, independently verified source/release provenance, signed approved Windows installer, exact WinGet package mapping, consented Windows package install/update/rollback, user rights and public deployment remain blocked. No synthetic fixture or temporary key can approve any of these.
