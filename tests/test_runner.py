from app.engine.runner import run_steps

# These rows mirror the seed `events` data, so the runner can be unit-tested
# without a database (run_steps is pure).
EVENTS = [
    {"id": 1, "user_id": "u1", "country": "US", "event_type": "purchase", "amount": 120},
    {"id": 2, "user_id": "u2", "country": "US", "event_type": "view", "amount": 0},
    {"id": 3, "user_id": "u3", "country": "IN", "event_type": "purchase", "amount": 40},
    {"id": 4, "user_id": "u1", "country": "US", "event_type": "purchase", "amount": 80},
]


def test_run_steps_executes_steps_in_order():
    rows, _ = run_steps(
        EVENTS,
        [
            {"type": "filter", "config": {"column": "event_type", "op": "eq", "value": "purchase"}},
            {"type": "select", "config": {"columns": ["user_id", "amount"]}},
        ],
    )
    assert len(rows) == 3
    assert all(set(row.keys()) == {"user_id", "amount"} for row in rows)


def test_run_steps_records_per_step_row_counts():
    _, step_stats = run_steps(
        EVENTS,
        [{"type": "filter", "config": {"column": "country", "op": "eq", "value": "US"}}],
    )
    assert step_stats == [{"step": "0:filter", "rows_out": 3}]
