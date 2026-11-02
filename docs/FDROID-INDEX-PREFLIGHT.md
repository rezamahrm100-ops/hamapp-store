# F-Droid signed-index v2 admission preflight

HamApp now has a fail-closed preflight built directly on **fdroidserver.index.download_repo_index_v2**. This avoids rewriting F-Droid's signature-verification and repository-index format.

To use it in a **trusted, isolated** environment, first obtain a canonical HTTPS repository URL and its signing certificate SHA-256 fingerprint independently from a trusted owner-controlled channel. Do not trust either value from a downloaded index or from a public PR.

The script requires:
- catalog/android_repository.json with a previously reviewed repository URL and 64-hex fingerprint, currently intentionally null.
- independent --expected-url and --expected-fingerprint values, which must match the recorded registry.
- a publicly resolvable canonical HTTPS hostname and /fdroid/repo/ path.
- the official fdroidserver Python library installed in the trusted environment at an audited/pinned version.
- upstream verification with verify_fingerprint=True, without any fallback to unsigned metadata.

Example (after real out-of-band approval):

    python scripts/verify_fdroid_signed_index.py --config reviewed.json \
      --expected-url https://approved.example.org/fdroid/repo/ \
      --expected-fingerprint OWNER_VERIFIED_64_HEX \
      --receipt signed-index-review.json

The script writes a **review-only** proof of a successfully verified index. It does not generate or store keys, publish an index, approve applications, verify developer APK certificates, install software, or enable public download buttons.

Unit tests mock fdroidserver deliberately: they check strict refusal behavior and API call contract, not a real signed index. No production repository is registered, therefore NO live cryptographic F-Droid index verification can be claimed yet.

A production release requires a persistent isolated repository signing identity, verified external trust fingerprint, secure offline backup, real signed app provenance, two-version installation/update, and independent publishing review.

Upstream official documentation: https://fdroid.gitlab.io/fdroidserver/fdroidserver.index.html
