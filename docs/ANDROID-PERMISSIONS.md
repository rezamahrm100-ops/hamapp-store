# Actual Android APK manifest permission review

The Android preview workflow now builds and signs the **actual DEBUG APK**, validates its package ID and exact version via the official Android SDK `aapt dump badging`, and independently executes `aapt dump permissions` on the produced bytes. An owner-reviewed allowlist (`catalog/android_preview_permission_policy.json`) lists permitted manifest permissions for the HamApp shell (initially empty). Unknown, malformed, duplicate, or undeclared permission requests cause the workflow to fail.

The validator creates a small safe receipt including the actual APK SHA256 and the discovered permission names, with `code_signature_verified=false`, `malware_free_verified=false` and `production_release_authorized=false`; no APK, signing key or user data are stored in this receipt.

Typical isolated manual check (Android SDK installed and no private production materials):

```bash
python3 scripts/android_permission_review.py --apk android/app/build/outputs/apk/debug/app-debug.apk --policy catalog/android_preview_permission_policy.json --aapt "$ANDROID_HOME/build-tools/35.0.0/aapt" --receipt /tmp/hamapp-android-permission-review.json
```

That is an honest static manifest-permission gate, **not** a sandbox behavioral malware analysis, a runtime-permission grant monitor, proof the package does not access sensitive data, a production signer verification or a publisher release approval. For genuine third-party publisher APKs the review policy must be independently owner-approved and combined with the existing signature, source attestation, active malware scan, human/legal review and physical/emulated update acceptance before enabling public downloads.
