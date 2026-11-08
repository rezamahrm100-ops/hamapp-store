# HamApp — single private publisher preflight from quarantine to signed F-Droid staging

## Active architecture

The existing local TLS publisher intake stores a real, bounded artifact in a
private owner-only POSIX quarantine; the incoming publisher name and source SHA
remain *unverified claims*. The existing `owner_candidate_intake` and
`fdroid_bridge.stage` already enforce independently registered package signer
identity, real Android `apksigner`/`aapt`, GitHub `gh attestation verify`
with immutable source/ref/workflow, actual ZIP/permission review, fresh
ClamAV malware signature scan, continuity/anti-rollback checks, official
`fdroid update` and a signed index-v2 verified against a separately pinned
repository certificate.

New `scripts/owner_verified_release_pipeline.py` connects them to an
**actual single owner-controlled transaction**:

1. Accept only a `review_requested` submission ID from the existing private
   quarantine, not an arbitrary pathname or user JSON claim.
2. Acquire a POSIX owner-only advisory lock shared with inbox hold/reject
   operations. A concurrent rejection cannot race signing/index updates.
3. Preflight the real quarantined APK, independently reviewed publisher
   registry/history and private 0700 F-Droid workspace with existing 0600
   `config.yml`; require independently pinned repository signer.
4. Call the **existing** `fdroid_bridge.stage` once. That method runs the
   actual OS APK signature, GitHub cryptographic provenance, archive integrity,
   aapt permissions and fresh ClamAV checks, builds upstream F-Droid signed
   metadata and independently verifies the signed JAR/index and APK bytes.
5. Revalidate quarantined file and chain after staging, then create a private
   0700 owner-only output directory containing an atomic 0600 audit receipt
   that binds the quarantine event chain, source SHA, exact artifact SHA256,
   registry/history digests and the signed index staging receipt.
6. If the signed workspace was updated but the final audit cannot be sealed,
   create a private `PUBLISHING_LOCKED_UNTIL_OWNER_REVIEW` marker. Never
   publish/replay a possibly inconsistent signed repository.

**No** public release, GitHub tag, PR merge, signed index upload, provenance
fabrication, authorisation or device install is triggered. The reviewer
must independently approve producer identity, license, privacy, malware
behavior, production repo key custody, signed HTTPS origin and physical
device acceptance before any future publication. Empty live signer registry
and release history deliberately prevent real production intake until
genuine owner-controlled identities are connected.

## Owner-local interface

This is an offline signing and review operation, not a new network listener.
Run only in the owner-controlled POSIX review environment with official
`fdroidserver`, `apksigner`, `aapt`, recent ClamAV and a GitHub CLI
supporting `gh attestation verify`. No installed production key or account
is inferred from a build artifact. Example (placeholders are not valid
production identities):

```bash
python scripts/owner_verified_release_pipeline.py \
  --private-inbox-root /secure/quarantine \
  --submission-id ACTUAL_32_HEX_SUBMISSION_ID \
  --fdroid-workspace /secure/signer-workspace \
  --registry /secure/owner-review/trusted_signers.json \
  --history /secure/owner-review/release_history.json \
  --android-permissions-policy /secure/owner-review/android-permissions.json \
  --trusted-workflow rezamahrm100-ops/real-source/.github/workflows/release.yml \
  --trusted-source-ref refs/tags/v1.2.3 \
  --expected-repo-fingerprint ACTUAL_INDEPENDENTLY_CHECKED_SHA256 \
  --output-dir /secure/owner-review/first-private-review
```

The existing Docker `publisher-intake` listener remains unchanged and
quarantine-only. This stage needs **separate private owner-held signing
workspace and external tools**, which are not included in the lightweight
intake service image. No production signer secret enters GitHub-hosted CI.
A Windows Authenticode candidate must be verified separately on a
native trusted Windows machine using existing `owner_candidate_intake`;
the Linux F-Droid signer route cannot certify Windows binaries.

## Acceptance scope

Hosted Linux and Windows unit tests exercise actual owner-only POSIX
folder/file modes, tamper detection, event-state locking, fail-closed
postflight locking and refusal to produce a public release. Mocked signature
results are labeled **synthetic**; real upstream signing is verified in
the separate signed-index and official F-Droid-client hosted fixture
workflows. No claim that genuine private publisher keys or paid marketplace
accounts have been activated.

The product-wide verdict remains PARTIAL; this closes the technical
coordination gap but does not close production signing, owner approval
or universal F-Droid client parity.
