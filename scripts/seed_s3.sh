#!/usr/bin/env bash
# Upload the source datasets to the S3 bucket the platform reads from.
#
# Usage:
#   export S3_BUCKET=your-bucket            # must already exist
#   export S3_PREFIX=dataflow-interview     # optional namespace within the bucket
#   export AWS_PROFILE=...                  # or AWS_ACCESS_KEY_ID / SSO, etc.
#   ./scripts/seed_s3.sh
set -euo pipefail

: "${S3_BUCKET:?set S3_BUCKET to a bucket you can write to}"

here="$(cd "$(dirname "$0")/.." && pwd)"
prefix="${S3_PREFIX:-}"
dest="s3://$S3_BUCKET${prefix:+/${prefix%/}}"

aws s3 cp "$here/seed/events.json" "$dest/events.json"
aws s3 cp "$here/seed/users.json"  "$dest/users.json"

echo "Seeded $dest (events.json, users.json)"
