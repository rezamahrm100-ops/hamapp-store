# Strict verified-only F-Droid staging — 2026-11-03

This change closes a substantive old-path security gap. Previously `scripts/fdroid_bridge.py` could run `fdroid update` after merely matching the local APK signer, bytes and version continuity. It did **not** require actual verified producer provenance, independent Android permissions, archive structural review or a fresh antivirus database. That narrower path is now removed from the stage API and CLI.

## Required *actual* evidence before `fdroid update`

`fdroid_bridge.stage()` now refuses an APK before copying any bytes unless all of the following are present in the owner-controlled private work environment:

- independently reviewed exact publisher identity in owner-provided signer registry and source/release history with anti-rollback checking;
- a pinned GitHub release workflow, full source digest and immutable SemVer tag, checked by genuine `gh attestation verify`;
- official Android SDK `apksigner` and `aapt` confirming exact signer, package ID, versionCode/versionName and permission allowlist;
- actual archive CRC, symlink/traversal and decompression bounds on the same APK;
- real ClamAV `clamscan` run with a recent signature database and unchanged SHA-256;
- a POSIX owner-owned private F-Droid workspace (0700) with non-symlink configuration file (0600); no public GitHub checkout, no existing filename overwrite.

The code rechecks the **copied** artifact and source hash immediately before upstream `fdroid update --create-metadata`, then rechecks the copied artifact after. A failed update or changed bytes removes the newly staged file. This stages only: it neither verifies the updated repository's production signing key, nor publishes it, nor modifies the public catalogue. The output expressly says `f_droid_signed_repository_independently_verified=false`, `deployed=false` and `owner_approved_for_public_distribution=false`.

## Owner-private command

```bash
python scripts/fdroid_bridge.py \
  --candidate /secure/owner-intake/candidate.json \
  --artifact /secure/owner-intake/verified.apk \
  --workspace /secure/private-fdroid-workspace \
  --registry /secure/owner-approved/trusted_signers.json \
  --history /secure/owner-approved/release_history.json \
  --trusted-workflow rezamahrm100-ops/approved-source/.github/workflows/release.yml \
  --trusted-source-ref refs/tags/v1.2.3 \
  --android-permissions-policy /secure/owner-approved/permissions.json \
  --antivirus-scanner clamscan \
  --receipt /secure/owner-review/fdroid-stage.json
```

Do **not** replace real production key, source, SHA, permission policy or certificate with CI test identities. Real production signing files belong only in owner-controlled private and backed-up workspace, never a GitHub-hosted PR runner or public repository.

After staging, separately verify the signed index-v2 with an independently pinned origin and repository key (`scripts/verify_fdroid_signed_index.py`), obtain actual owner approval and perform official F-Droid client install/upgrade/rollback QA before activating the public catalogue. A correct staging result **is not approval to distribute software**.

## Tests

Hosted Linux and Windows regression tests use patched stand-in signatures/antivirus **only** to prove that old bypasses are no longer reachable and to exercise rollback, missing producer policy, spoofed antivirus digest, malicious source mutation and upstream failure handling. The existing actual Android debug APK/F-Droid signed-index integration workflows remain independent real engineering evidence; only real owner-supplied signed software can satisfy production preflight. The public signer registry and app download history remain empty.
