# ClamAV actual binary signature screening — 2026-11-03

Owner-local binary preflight now integrates actual upstream **ClamAV `clamscan`** against the exact APK/EXE/MSI/MSIX file. The scan is not a substitute for signed producer provenance, OS publisher certificate verification, independently reviewed Android permissions, sandbox behavior review, legal/license checks, owner GitHub review or real device install/update acceptance.

`scripts/antivirus_binary_review.py` verifies actual file is a non-symlink bounded regular binary, requires an installed scanner with a **signature DB dated no more than 14 days earlier** (no missing DB, no silent stale scan), runs ClamAV with `shell=False`, bounded output and timeout, rejects signatures/detections/scan failures, then SHA-256 rechecks the same file against the initial bytes. Receipt contains only public-safe hash, size, engine and signature DB version/date, and explicitly `malware_absence_verified=false` and `public_distribution_authorized=false`.

Owner-local review with a genuine approved publisher candidate:

```bash
python scripts/owner_candidate_intake.py \
 --candidate /secure/owner-intake/candidate.json \
 --artifact /secure/owner-intake/release.apk \
 --publisher-registry /secure/owner-intake/approved-publishers.json \
 --release-history /secure/owner-intake/history.json \
 --android-permissions-policy /secure/owner-intake/android-policy.json \
 --trusted-workflow approved/repo/.github/workflows/release.yml \
 --trusted-source-ref refs/tags/v1.2.3 \
 --antivirus-scanner clamscan \
 --output-dir /secure/owner-intake/review
```

The CLI now requires actual ClamAV scan by default, in addition to signature/provenance/archive/permission checks. A mismatch or unavailable/stale database fails the review; it never accepts a user-supplied JSON scanner report as proof. No private candidate or key is uploaded to public CI.

## Real hosted Android preview evidence

The dedicated `.github/workflows/android-binary-antivirus.yml` uses official Ubuntu packages, requires `freshclam` to refresh the real DB, builds an actual native first-party **DEBUG** APK on a hosted runner, and runs this scanner on its exact bytes. This job can fail on upstream DB download outages; **do not** convert such outages to successful malware scans or disable required DB freshness. Only a `completed/success` run plus a safe receipt is accepted evidence.

**ClamAV signatures do not prove the absence of malicious Android code, spyware, dynamic downloaders, exploit behavior or abuse of legitimate permissions.** A clean result indicates only no matched signatures with the specified database at the observed time. Production real private publisher packages and owner keys never belong on a public runner. Additional sandbox/manual review and approved real signing identities are still mandatory.

Local direct CLI (after installing and updating ClamAV in a private environment):

```bash
python scripts/antivirus_binary_review.py --artifact /secure/inbox/approved.apk --scanner clamscan --receipt /secure/reviews/clamav.json
```
