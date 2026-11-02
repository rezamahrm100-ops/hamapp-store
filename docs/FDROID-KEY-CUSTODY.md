# Owner-controlled F-Droid signing key custody — independent-volume backup

This tool is **not run by public CI on real owner keys**. It makes a private, byte-for-byte backup of an existing F-Droid keystore (JKS/PKCS12) to an independently mounted volume and independently re-hashes the source and copy. It never generates production identities, reads keystore passwords, uploads assets, prints fingerprints or authorizes publishing. Physical disconnection, encrypted-at-rest custody and actual successful restore/signing require separate owner validation.

## Owner-only offline execution

Use an **isolated POSIX signer environment**, with the genuine source key file permission 0600, and a mounted **different filesystem/device** containing an existing private 0700 directory. Confirm the offline target is encrypted and disconnectable. Paths must be outside the HamApp public source checkout. Do not mount or expose private keys to a public GitHub Actions runner.

```bash
python3 scripts/fdroid_key_custody.py \
  --keystore /private/signer/repo-key.jks \
  --offline-backup-dir /media/offline-secure/hamapp-repo-key \
  --backup-name repo-key-backup.jks \
  --receipt /media/offline-secure/hamapp-repo-key/custody-receipt.json
```

The tool requires different `st_dev`, checks source file 0600 (or stricter), denies symlinks, rejects an existing backup path, atomically creates the file with mode 0600, syncs and independently verifies byte parity. It refuses Windows because equivalent ACL validation is not implemented. A same-disk copy cannot masquerade as independent backup. The safe receipt contains booleans only and explicitly says physical offlining, restore/signing and production publication are **not yet verified**.

Owner still must independently test recovery of this backup in an isolated signer workstation and verify a newly signed official F-Droid v2 index with an out-of-band trusted fingerprint. Never place the key, password, offline backup or receipt in public repository/CI uploads.

## Tests and security boundaries

`python -m unittest discover -s tests -v` includes POSIX-only throwaway fixture bytes for backup/mismatch/permissions/symlink/path traversal/duplicate denial. Fake bytes **are not** signing keys; the tests inject a simulated second volume because GitHub CI cannot attest physical backup custody. This is meaningful backup handling validation, NOT proof a production key has been backed up.

The public Android repository registry remains null, and production signers remain empty until independent owner-controlled commissioning and signed-index/device acceptance.
