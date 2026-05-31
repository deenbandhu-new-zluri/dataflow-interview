"""Postgres access.

A single lazily-opened connection pool is shared across the process. Use the
``get_connection()`` context manager for a pooled connection whose cursors
return rows as ``dict``s.
"""

from __future__ import annotations

from contextlib import contextmanager

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from .config import DATABASE_URL

# Opened on first use rather than at import time, so the app/tests can be
# imported without a database being reachable.
_pool: ConnectionPool | None = None


def _get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            DATABASE_URL, min_size=1, max_size=10, open=True, kwargs={"row_factory": dict_row}
        )
    return _pool


@contextmanager
def get_connection():
    with _get_pool().connection() as conn:
        yield conn
