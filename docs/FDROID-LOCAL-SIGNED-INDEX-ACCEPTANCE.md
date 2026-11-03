# F-Droid local signed index-v2 and exact APK validation — 2026-11-03

The owner-private F-Droid stage previously accepted a successful `fdroid update` command without checking that the resulting signed `entry.jar` commits to an index-v2 listing **the exact approved APK digest, versionCode, package ID and size**. This left a gap between input package validation and generated signed repository contents.

`scripts/verify_fdroid_private_stage.py` now uses the **official `fdroidserver.index.get_index_from_jar`** signature-verification function. The operator supplies a separately approved SHA-256 repository certificate fingerprint. The validator requires matching signer fingerprint, a genuine upstream signature-verification result for `entry.jar`, the signed entry's exact `index-v2.json` SHA-256 and byte size, then finds **exactly one** indexed version matching the independently checked candidate's APK hash, size, Android package ID, versionCode and versionName.

This verifier operates entirely on files in an owner-controlled private POSIX workspace. It **does not** serve signing config/keystore over HTTP, invent or store production signing identities, publish an index, assert a live HTTPS origin, approve a developer, or install an APK.

## How private staging changed

`scripts/fdroid_bridge.py` now requires `--expected-repo-fingerprint` in addition to actual publisher signature, GitHub source attestation, Android permissions, archive checks and fresh ClamAV signatures. After upstream `fdroid update`, a second independent signature and APK-index consistency check must succeed. A failed or missing signed index removes the just-staged APK and creates a private `PUBLISHING_LOCKED_UNTIL_OWNER_REVIEW` marker. The signed metadata could have been mutated already; the tool **does not falsely claim to roll it back**. The owner must inspect/recover the workspace from a verified backup, reissue a signed index, and independently validate it before any distribution. Another stage cannot bypass the lock.

The initial repository certificate is still a genuine owner-controlled, out-of-band trust root. Merely supplying any 64-digit fingerprint at the CLI is not owner approval. The public GitHub registry remains empty and signed public HTTPS origin/official F-Droid subscription and device update are still unverified.

## Private staging CLI

```bash
python scripts/fdroid_bridge.py \
  --candidate /secure/owner-intake/candidate.json \
  --artifact /secure/owner-intake/verified.apk \
  --workspace /secure/private-fdroid \
  --registry /secure/owner-approved/trusted_signers.json \
  --history /secure/owner-approved/release_history.json \
  --trusted-workflow rezamahrm100-ops/approved-source/.github/workflows/release.yml \
  --trusted-source-ref refs/tags/v1.2.3 \
  --android-permissions-policy /secure/owner-approved/permissions.json \
  --expected-repo-fingerprint <out-of-band-approved-64-hex-repo-key> \
  --antivirus-scanner clamscan \
  --receipt /secure/review/private-stage.json
```

The receipt reports `private_index_v2_signature_and_exact_apk_verified=true` on verified local bytes, but explicitly reports public HTTPS repository verification and out-of-band owner approval as false. No publishing action is performed.

## Real integration evidence vs fixtures

`tests/test_verify_fdroid_private_stage.py` covers forged signer, altered signed entry SHA, missing signed index, wrong APK version/digest/size and duplicate entries using clearly synthetic loader fixtures. These fixtures are **not evidence of cryptographic signing**.

The existing `HamApp Isolated F-Droid Signed Index Drill` is extended to run on reviewable same-repository PRs using **GitHub-hosted** disposable signing keys only. It builds a real debug APK, invokes upstream `fdroid update`, verifies the signed v2 index with the upstream downloader, and now separately checks the local signed JAR and exact APK using this validator. It destroys all temporary credentials and publishes only bounded no-secret receipt. Check actual workflow success and unchanged SHA for any acceptance claim; no real production key, production origin, official F-Droid client subscription or owner-device test is included.

Current authoritative F-Droid index format: <https://fdroid.gitlab.io/fdroidserver/fdroidserver.index.html>. The official signature-verification method is reused rather than reimplementing JAR cryptography.

## Actual indexed package bytes are now mandatory (2026-11-03)

A valid signed `index-v2.json` can still reference an APK missing from its own repository directory, or a file whose bytes were replaced after index generation. The local private acceptance therefore additionally requires the signed version record to contain exactly one safe single-component `/*.apk` path, a non-symlink, non-hardlinked regular file physically present under `workspace/repo/`, and a full streaming SHA-256 and size check of **those actual downloadable bytes** against the independently approved candidate. A signed metadata claim alone is no longer sufficient. Negative tests cover absent files, actual-byte corruption, symlink substitution, unsafe filenames and mismatched candidate entries.

This source check remains private/offline. It does not verify an externally deployed HTTPS mirror retains these bytes, provide independent publisher approval or perform real official F-Droid client installation. The two-version disposable real signed-index integration is documented in `docs/FDROID-ISOLATED-SIGNED-INDEX-DRILL.md` and must pass its exact GitHub Actions run before acceptance.
