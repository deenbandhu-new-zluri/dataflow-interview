"""Pipeline execution engine."""

from __future__ import annotations

from datetime import datetime, timezone

from ..operators import apply_step
from ..sources import get_source

Rows = list[dict]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_steps(rows: Rows, steps: list[dict]) -> tuple[Rows, list[dict]]:
    """Fold the operator steps over ``rows`` (pure — no I/O).

    Returns the transformed rows and a per-step record of how many rows each
    step emitted, so a run is debuggable.
    """
    step_stats: list[dict] = []
    for index, step in enumerate(steps):
        rows = apply_step(rows, step)
        step_stats.append({"step": f"{index}:{step['type']}", "rows_out": len(rows)})
    return rows, step_stats


def execute(pipeline: dict) -> dict:
    """Run a pipeline definition and return a run result.

    A pipeline is::

        {"source": str, "steps": [{"type": str, "config": {...}}, ...]}

    Loads rows from the source, folds the steps over them, and stamps timing.
    """
    started_at = _now()
    source = get_source(pipeline["source"])

    rows = source.read()
    source_stat = {"step": f"source:{source.name}", "rows_out": len(rows)}

    rows, step_stats = run_steps(rows, pipeline["steps"])

    return {
        "status": "success",
        "started_at": started_at,
        "finished_at": _now(),
        "row_count": len(rows),
        "step_stats": [source_stat, *step_stats],
        "output": rows,
    }
