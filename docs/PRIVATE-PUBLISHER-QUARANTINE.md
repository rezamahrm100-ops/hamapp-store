# Owner-private publisher submission quarantine — 2026-11-03

This is an **owner-controlled local intake queue**, not a production web portal, public upload API or authenticated multi-tenant service. It uses Python standard library and a POSIX filesystem (Linux / WSL2) and never downloads, executes, approves or publishes untrusted program files. It can store submissions before authentic publisher identity is established. Never run this in a public PR workflow with real apps, developer keys or personal data.

## Architecture

- The operator creates a **new** root directory outside the public HamApp checkout, mode 0700, owned by the current POSIX user. Inputs cannot be symlinks or hardlinks and must reside outside that root.
- A submission claims a source repository, source SHA, Android package ID or Windows platform. The claims must be syntactically consistent with the approved shape of a GitHub release URL, **but are not proof of publisher identity**.
- The real APK/EXE/MSIX is copied in bounded streaming into a uniquely random 128-bit submission directory (0700) with mode-0600 files and fsync. It is checked against the submission's exact declared size and SHA-256 both before and after the copy. APK and MSIX archive structure is independently inspected without unpacking or running binaries.
- The submission and its original candidate metadata are stored as private data with all publisher authentication, signing, scanning and release flags **false**.
- Separate non-approving lifecycle markers `request_review`, `hold`, and terminal `reject` are appended as consecutive small event files with previous-record SHA-256 links. This exposes accidental corruption, not proof of identity or cryptographically authenticated review. There is deliberately **no approve/publish transition**.
- Only a `request_review` submission with verified exact local bytes and source metadata can be passed into the existing `owner_candidate_intake.py`. That tool still checks independently pinned real signer certificates, GitHub attestation, actual archive/Android permissions and fresh ClamAV signatures; it produces a **review-only receipt**, without modifying GitHub or enabling a download.

## Commands — local private POSIX machine only

Initialize the vault once in an existing secure parent directory:

```bash
python3 scripts/private_publisher_inbox.py init --root /secure/hamapp-private-intake
```

The root must not exist yet, and cannot be inside the public GitHub working tree. The filesystem's confidentiality, disk encryption, backup, root ownership and user access controls remain the operator's responsibility.

Receive a locally obtained APK or Windows installer, where the candidate JSON describes its exact immutable GitHub release, source SHA, platform, sha256, and size:

```bash
python3 scripts/private_publisher_inbox.py stage \
  --root /secure/hamapp-private-intake \
  --candidate /secure/incoming/candidate.json \
  --artifact /secure/incoming/release.apk \
  --claimed-publisher example-repo
```

The command prints a random **submission ID**, an untrusted claim, and explicit no-approval metadata. No GitHub upload is triggered.

Mark it for local technical review (or `hold` / `reject`):

```bash
python3 scripts/private_publisher_inbox.py mark \
  --root /secure/hamapp-private-intake \
  --id <32-lowercase-hex-submission-id> \
  --event request_review
```

Then use the **same immutable private copy** for the actual cryptographic and antivirus checks:

```bash
python3 scripts/owner_candidate_intake.py \
  --private-inbox-root /secure/hamapp-private-intake \
  --submission-id <same-submission-id> \
  --publisher-registry /secure/owner-approved/trusted_signers.json \
  --release-history /secure/owner-approved/release_history.json \
  --android-permissions-policy /secure/owner-approved/app-permissions.json \
  --trusted-workflow rezamahrm100-ops/example-repo/.github/workflows/release.yml \
  --trusted-source-ref refs/tags/v1.2.3 \
  --aapt /opt/android-sdk/build-tools/35.0.0/aapt \
  --antivirus-scanner clamscan \
  --output-dir /secure/owner-reviewed/new-review-receipt
```

For Windows binaries omit `--android-permissions-policy`, and perform the Authenticode verification on a native owner-controlled Windows session. A POSIX staging vault does not magically provide Windows native Authenticode verification; the owner must transfer the same verified bytes through an authorized private mechanism and recheck their SHA-256 on the native Windows signer-verification host. A staged filename and metadata **do not prove authorship**, because no remote account authentication has been configured.

## Negative tests and acceptance

`python3 -m unittest discover -s tests -v` includes actual Linux filesystem tests of bounded copy, mode 0700/0600, untrusted identity, incorrect hashes, symlinks/hardlinks, replay identifiers, unsafe paths, append-only *logical* event continuity, tampering, rejection and real local CLI handoff. Windows runs skip POSIX-only tests and still execute the rest of the suite. Hosted CI tests synthetic sample APK/EXE bytes only; these are **not** genuine approved publisher submissions.

## Remaining engineering and owner gates

Still required: authenticated publisher identities/accounts, per-publisher authorization and resource quotas, private HTTPS intake service and encrypted-at-rest production storage (only if actually authorized and deployed); externally certified signer fingerprints and developer keys; trusted GitHub producer attestations; runtime malicious-behavior, privacy, licensing and vulnerability review; stable production F-Droid repository key/index and owner-approved device installation; real Windows Authenticode cert, mapping and device upgrade; and enforced GitHub branch protection/owner review Issue #31. The public catalog trust registry and releases remain empty until independently approved. A private queue entry, even with `request_review`, **never approves publication**.
