#!/bin/sh
# Only invoked by explicitly chosen Compose profile "owner-review".
# Signature database stays in the owner-only bind mount; never in image/logs.
set -eu
umask 077
test -d /owner || { echo "PRIVATE_OWNER_REVIEW_VOLUME_MISSING" >&2; exit 19; }
mkdir -p /owner/clamav-database
test -w /owner/clamav-database || { echo "OWNER_CLAMAV_DATABASE_NOT_WRITABLE" >&2; exit 19; }
# Must fail closed if network/ClamAV DB freshness cannot be established.
freshclam --quiet --datadir=/owner/clamav-database >/dev/null \
  || { echo "OWNER_ANTIVIRUS_DATABASE_UPDATE_FAILED" >&2; exit 20; }
# The image's fixed /usr/local/bin/clamscan wrapper binds the owner-only DB;
# no scripts are executed out of a writable /tmp filesystem.
exec python3 -B /opt/hamapp/scripts/owner_verified_release_pipeline.py "$@"
