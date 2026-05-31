"""Runtime configuration, read from the environment.

A local ``.env`` file (gitignored) is loaded if present, so secrets live there
rather than in source.
"""

import os

from dotenv import load_dotenv

load_dotenv()

# Connection string for the platform's Postgres book-keeping store (see
# docker-compose.yml for the local default).
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://dataflow:dataflow@localhost:5432/dataflow",
)

# S3 holds the source datasets. Credentials resolve through the standard AWS
# chain (env vars, shared config, SSO, instance role) — only set the *_KEY env
# vars below to override it. S3_BUCKET must point at a bucket seeded with the
# source objects (see scripts/seed_s3.sh); S3_PREFIX namespaces them within it.
S3_BUCKET = os.environ.get("S3_BUCKET", "dataflow-sources")
S3_PREFIX = os.environ.get("S3_PREFIX", "")
AWS_REGION = os.environ.get("AWS_REGION", "us-west-2")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID") or os.environ.get("AWS_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY") or os.environ.get("AWS_SECRET_KEY")
AWS_SESSION_TOKEN = os.environ.get("AWS_SESSION_TOKEN")

# Optional: override the S3 endpoint (e.g. for a local emulator). Left unset,
# boto3 talks to real AWS S3.
S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL")
