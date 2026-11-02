# Real local publisher binary intake and archive security — November 3, 2026

The **public static storefront does not accept uploads and is not an authentication server**. A trusted owner performs this preflight separately, on the exact local signed production artifact and a signer registry whose fingerprints were approved independently. No GitHub-hosted PR runner or owner self-hosted public PR receives production binaries, private keys or credentials.

## Actual local preflight (review only)

Required tools: official `gh` CLI authenticated to a repository the owner is authorized to review, Android SDK `apksigner` and `aapt` for Android, or native Windows PowerShell Authenticode for Windows. Use an artifact whose signed GitHub provenance was issued by its authorized producer and source SHA. The source repo/tag/workflow cannot be arbitrary; reviewer must independently pin them.

```bash
python scripts/owner_candidate_intake.py \
  --candidate /secure/owner-intake/candidate.json \
  --artifact /secure/owner-intake/release.apk \
  --publisher-registry /secure/owner-intake/approved-publishers.json \
  --release-history /secure/owner-intake/history.json \
  --android-permissions-policy /secure/owner-intake/approved-android-permissions.json \
  --aapt /path/to/android-sdk/build-tools/35.0.0/aapt \
  --trusted-workflow owner/repository/.github/workflows/release.yml \
  --trusted-source-ref refs/tags/v1.2.3 \
  --output-dir /secure/owner-intake/new-review-receipt
```

This command must fail with the repository's public empty trust registry; that is deliberate. The real owner-managed registry may contain only the independently verified package/Windows signer identity. The workflow and GitHub attestation must match local bytes and the exact immutable source SHA/ref. OS `apksigner` / Windows `Get-AuthenticodeSignature` must validate its signer against the pinned publisher registry. For Android, official `aapt` verifies package ID, versionCode/versionName and the independently approved manifest permission allowlist.

## Actual ZIP archive structural review

`scripts/binary_archive_review.py` runs against the **actual** built APK in hosted Android preview, and against locally supplied APK/MSIX/MSIXBUNDLE in the owner preflight. It reads every compressed entry and verifies CRC without extraction or app execution, rejects traversal/absolute/doubly-slash/drive/ambiguous paths, Unicode/case-insensitive duplicate names, symlink entries, encrypted entries, nonstandard compression and overlarge decompression/ratios. Re-hashes actual bytes before and after. A small hash/structure-only receipt is a short-lived GitHub artifact for the public debug APK.

Standalone invocation:

```bash
python scripts/binary_archive_review.py --artifact /private/input/reviewed.apk --receipt /private/output/archive-review.json
```

**What it does NOT prove:** absence of malware or executable malicious behavior, absence of data exfiltration, verified publisher approval, installer code-signing or permission changes after installation. For EXE/MSI the ZIP structure check is not applicable; native Authenticode signature remains the relevant integrity tool. Even a clean result must never authorize a public release.

## Remaining owner gates

Require independent actual malware/behavior and privacy/license review on exact bytes, approved signing-key custody and F-Droid index/root or Windows signature chain as appropriate, real two-version install/update and rollback testing on an authorized device, GitHub PR author/reviewer authorization with enforced repository branch ruleset (Issue #31), and exact approved catalogue/history atomic promotion. None of these are automatically completed or bypassed by intake receipt booleans. No real production signer or download is registered in the public store.

## Tests

Hosted Linux/Windows source tests exercise archive corruption, path traversal, ZIP bombs, duplicates, POSIX symlinks, fail-closed missing permission policy, and byte mutation during intake; **those synthetic tests alone are not production signing acceptance**. Android native preview workflow independently validates the real built APK with official Android SDK and actual archive bytes. See the exact run/commit results rather than inferring that the workflow ran merely because YAML exists.
