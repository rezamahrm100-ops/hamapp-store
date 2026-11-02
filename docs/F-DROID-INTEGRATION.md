# Upstream F-Droid integration: prepared, NOT launched

## Reuse choice

We use upstream [`fdroidserver`](https://f-droid.org/docs/Setup_an_F-Droid_App_Repo/) instead of writing an Android index, signing and update protocol. F-Droid is a full open-source ecosystem, and self-managed binary repositories are documented upstream. Future native Android client options include reusing the existing F-Droid client under the applicable GPL conditions.

## Trusted signer boundary

The production Android **repository** key must live on a trusted owner-controlled device or isolated machine with a separate backup. The APK itself is signed by its own developer release key. Never put either key in a public GitHub repository, Pages artifact, workflow artifact, logs or plaintext Actions secret. Do not regenerate the repository key on each CI run; this invalidates the trust root. Do not accept unknown APKs from GitHub Release links without ownership and APK signing-certificate verification.

## Next engineering steps

1. Prepare a separate private/offline F-Droid workspace on a dedicated trusted host; install upstream `fdroidserver`, JDK and Android build tools from verified packages.
2. Set up persistent F-Droid repo key with offline backup and publish its fingerprint through an independent trusted channel.
3. Ingest a real release with package name, signing certificate fingerprint, version code and SHA256; run `fdroid update` from a secure workspace.
4. Publish `repo/` over HTTPS, preserving signed index and XML/JSON metadata, and verify subscription in the official F-Droid client.
5. Automate release intake only from allowlisted upstream repositories, after tagged-release review, reproducible builds, malware scan and signature verification.
6. Before using a branded client, preserve GPL compliance (license text, notices, complete corresponding source, brand/trademark distinctions, and distribution obligations).

Until these gates pass, the store website will NOT claim that it can install or automatically update Android apps. No F-Droid keystore or active signed repository is in this bootstrap.

## Signed-index admission CLI

Before enabling a repository, use [the official index-v2 verification wrapper](FDROID-INDEX-PREFLIGHT.md). It explicitly invokes fdroidserver.index.download_repo_index_v2 with verify_fingerprint=True and a fingerprint independently pinned by owner approval. `catalog/android_repository.json` remains null until a genuine securely signed HTTPS repository is available and independently audited. This wrapper creates no keystore or live F-Droid repo.
