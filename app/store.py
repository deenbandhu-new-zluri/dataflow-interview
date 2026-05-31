"""Persistence for pipelines and runs, backed by Postgres."""

from __future__ import annotations

from psycopg.types.json import Jsonb

from .db import get_connection
from .errors import NotFoundError


class Store:
    # --- pipelines ---------------------------------------------------------

    def create_pipeline(self, name: str, source: str, steps: list[dict]) -> dict:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO pipelines (name, source, steps)
                VALUES (%s, %s, %s)
                RETURNING *
                """,
                (name, source, Jsonb(steps)),
            )
            return cur.fetchone()

    def get_pipeline(self, pipeline_id: int) -> dict:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM pipelines WHERE id = %s", (pipeline_id,))
            pipeline = cur.fetchone()
        if pipeline is None:
            raise NotFoundError(f"No pipeline with id {pipeline_id}")
        return pipeline

    def list_pipelines(self) -> list[dict]:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM pipelines ORDER BY id")
            return cur.fetchall()

    # --- runs --------------------------------------------------------------

    def create_run(self, pipeline_id: int, result: dict) -> dict:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO runs
                    (pipeline_id, status, started_at, finished_at, row_count, step_stats, output)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (
                    pipeline_id,
                    result["status"],
                    result["started_at"],
                    result["finished_at"],
                    result["row_count"],
                    Jsonb(result["step_stats"]),
                    Jsonb(result["output"]),
                ),
            )
            return cur.fetchone()

    def get_run(self, run_id: int) -> dict:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM runs WHERE id = %s", (run_id,))
            run = cur.fetchone()
        if run is None:
            raise NotFoundError(f"No run with id {run_id}")
        return run


store = Store()
