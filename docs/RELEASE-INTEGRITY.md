# HamApp release integrity gate

This module performs OFFLINE verification of a proposed release against a separately owner-approved manifest.

It rejects invalid metadata, untrusted hostnames, mismatched GitHub release tags, misleading file extensions, file size mismatches and SHA-256 mismatches. It does not download, run, install, sign or publish files.

Required manifest fields: app_id, platform, version, asset_url, sha256, size_bytes. The asset URL must be an owner-controlled GitHub versioned release download; the hash must originate from a trustworthy, independent source.

Run:

    python scripts/release_integrity.py --manifest candidate.json --artifact candidate.apk --output audit-receipt.json

The receipt explicitly returns signature_verified: false. A passing hash is NOT proof of publisher identity and must never automatically enable download links in the public catalogue.

Production publishing additionally requires APK signing certificate checks or Windows Authenticode checks, identity continuity, provenance, malware review, real installation/update tests, and publisher authorization. The F-Droid signing key belongs on a separate controlled device. See F-DROID-INTEGRATION.md.
