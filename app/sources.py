"""Source connectors.

Each source is a named, read-only dataset stored as a JSON object in S3. A
source exposes ``read()``, which fetches its object and returns the rows as a
list of plain ``dict``s. Credentials and bucket come from ``config`` / the
standard AWS credential chain.

(Postgres backs the platform's *book-keeping* — pipelines and runs, see
``store.py`` — not these source datasets.)
"""

from __future__ import annotations

import json

import boto3

from .config import (
    AWS_ACCESS_KEY_ID,
    AWS_REGION,
    AWS_SECRET_ACCESS_KEY,
    AWS_SESSION_TOKEN,
    S3_BUCKET,
    S3_ENDPOINT_URL,
    S3_PREFIX,
)
from .errors import NotFoundError

Row = dict
Rows = list[Row]

# Source name -> object file name in the S3 bucket.
_SOURCE_KEYS = {
    "events": "events.json",
    "users": "users.json",
}


def _client():
    kwargs = {"region_name": AWS_REGION}
    # Only override these if explicitly configured; otherwise boto3 resolves the
    # endpoint (real AWS) and credentials (env, shared config, SSO, IAM role) on
    # its own.
    if S3_ENDPOINT_URL:
        kwargs["endpoint_url"] = S3_ENDPOINT_URL
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        kwargs["aws_access_key_id"] = AWS_ACCESS_KEY_ID
        kwargs["aws_secret_access_key"] = AWS_SECRET_ACCESS_KEY
        if AWS_SESSION_TOKEN:
            kwargs["aws_session_token"] = AWS_SESSION_TOKEN
    return boto3.client("s3", **kwargs)


class Source:
    def __init__(self, name: str, key: str):
        self.name = name
        self._key = key

    def read(self) -> Rows:
        client = _client()
        body = client.get_object(Bucket=S3_BUCKET, Key=self._key)["Body"].read()
        return json.loads(body)


def get_source(name: str) -> Source:
    file_name = _SOURCE_KEYS.get(name)
    if file_name is None:
        available = ", ".join(_SOURCE_KEYS)
        raise NotFoundError(f'Unknown source: "{name}". Available: {available}')
    key = f"{S3_PREFIX.rstrip('/')}/{file_name}" if S3_PREFIX else file_name
    return Source(name, key)


def source_names() -> list[str]:
    return list(_SOURCE_KEYS)
