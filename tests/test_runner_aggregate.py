"""Integration tests for runners with aggregate operator.

Tests the aggregate operator in the runner, including step statistics
and row count tracking.
"""

from app.engine.runner import run_steps

# Test data mirroring seed events
EVENTS = [
    {"id": 1, "user_id": "u1", "country": "US", "event_type": "purchase", "amount": 120},
    {"id": 2, "user_id": "u2", "country": "US", "event_type": "view", "amount": 0},
    {"id": 3, "user_id": "u3", "country": "IN", "event_type": "purchase", "amount": 40},
    {"id": 4, "user_id": "u1", "country": "US", "event_type": "purchase", "amount": 80},
    {"id": 5, "user_id": "u4", "country": "IN", "event_type": "view", "amount": 0},
    {"id": 6, "user_id": "u5", "country": "DE", "event_type": "purchase", "amount": 200},
    {"id": 7, "user_id": "u2", "country": "US", "event_type": "refund", "amount": -30},
    {"id": 8, "user_id": "u3", "country": "IN", "event_type": "purchase", "amount": 60},
]


def test_run_steps_executes_steps_in_order():
    """Test that multiple steps execute in correct order."""
    rows, _ = run_steps(
        EVENTS,
        [
            {"type": "filter", "config": {"column": "event_type", "op": "eq", "value": "purchase"}},
            {"type": "select", "config": {"columns": ["user_id", "amount"]}},
        ],
    )
    assert len(rows) == 5
    assert all(set(row.keys()) == {"user_id", "amount"} for row in rows)


def test_run_steps_records_per_step_row_counts():
    """Test that step statistics are recorded correctly."""
    _, step_stats = run_steps(
        EVENTS,
        [{"type": "filter", "config": {"column": "country", "op": "eq", "value": "US"}}],
    )
    assert step_stats == [{"step": "0:filter", "rows_out": 4}]


# ============================================================================
# AGGREGATE OPERATOR RUNNER TESTS
# ============================================================================


class TestAggregateRunnerSingleGroupBy:
    """Tests for aggregate operator in runner with single groupBy column."""

    def test_aggregate_single_groupby_single_agg(self):
        """Test aggregate with single groupBy and single aggregation."""
        rows, step_stats = run_steps(
            EVENTS,
            [
                {
                    "type": "aggregate",
                    "config": {
                        "groupBy": ["country"],
                        "aggregations": [{"column": "amount", "op": "sum", "as": "total"}],
                    },
                }
            ],
        )
        assert len(rows) == 3  # US, IN, DE
        assert len(step_stats) == 1
        assert step_stats[0] == {"step": "0:aggregate", "rows_out": 3}

        # Verify aggregated values
        by_country = {r["country"]: r for r in rows}
        assert by_country["US"]["total"] == 120 + 0 + 80 - 30  # 170
        assert by_country["IN"]["total"] == 40 + 0 + 60  # 100
        assert by_country["DE"]["total"] == 200

    def test_aggregate_single_groupby_multiple_aggs(self):
        """Test aggregate with multiple aggregations."""
        rows, _ = run_steps(
            EVENTS,
            [
                {
                    "type": "aggregate",
                    "config": {
                        "groupBy": ["country"],
                        "aggregations": [
                            {"column": "amount", "op": "sum", "as": "total_amount"},
                            {"column": "id", "op": "count", "as": "events"},
                            {"column": "amount", "op": "avg", "as": "avg_amount"},
                        ],
                    },
                }
            ],
        )
        assert len(rows) == 3
        by_country = {r["country"]: r for r in rows}

        # US: ids 1,2,4,7 with amounts 120,0,80,-30
        us = by_country["US"]
        assert us["total_amount"] == 170
        assert us["events"] == 4
        assert us["avg_amount"] == 170 / 4

        # IN: ids 3,5,8 with amounts 40,0,60
        in_row = by_country["IN"]
        assert in_row["total_amount"] == 100
        assert in_row["events"] == 3
        assert in_row["avg_amount"] == 100 / 3

        # DE: id 6 with amount 200
        de = by_country["DE"]
        assert de["total_amount"] == 200
        assert de["events"] == 1
        assert de["avg_amount"] == 200

    def test_aggregate_all_operations(self):
        """Test all aggregation operations: sum, count, avg, min, max."""
        rows, _ = run_steps(
            EVENTS,
            [
                {
                    "type": "aggregate",
                    "config": {
                        "groupBy": ["country"],
                        "aggregations": [
                            {"column": "amount", "op": "sum", "as": "total"},
                            {"column": "amount", "op": "count", "as": "count"},
                            {"column": "amount", "op": "avg", "as": "avg"},
                            {"column": "amount", "op": "min", "as": "min"},
                            {"column": "amount", "op": "max", "as": "max"},
                        ],
                    },
                }
            ],
        )
        assert len(rows) == 3
        by_country = {r["country"]: r for r in rows}

        # US: amounts [120, 0, 80, -30]
        us = by_country["US"]
        assert us["total"] == 170
        assert us["count"] == 4
        assert us["avg"] == 170 / 4
        assert us["min"] == -30
        assert us["max"] == 120


class TestAggregateRunnerMultipleGroupBy:
    """Tests for aggregate operator with multiple groupBy columns."""

    def test_aggregate_multiple_groupby(self):
        """Test aggregate with multiple groupBy columns."""
        rows, step_stats = run_steps(
            EVENTS,
            [
                {
                    "type": "aggregate",
                    "config": {
                        "groupBy": ["country", "id"],
                        "aggregations": [
                            {"column": "amount", "op": "sum", "as": "total_amount"},
                            {"column": "id", "op": "count", "as": "events"},
                        ],
                    },
                }
            ],
        )
        # Each row has unique id, so we get 8 groups (one per event)
        assert len(rows) == 8
        assert step_stats[0] == {"step": "0:aggregate", "rows_out": 8}

        # Find and verify US-1 group (id 1, country US)
        us_1 = next((r for r in rows if r["country"] == "US" and r["id"] == 1), None)
        assert us_1 is not None
        assert us_1["total_amount"] == 120
        assert us_1["events"] == 1

    def test_aggregate_multiple_groupby_with_duplicates(self):
        """Test aggregate with multiple groupBy where groups have multiple rows."""
        # Create test data with duplicate country-event_type pairs
        test_data = [
            {"id": 1, "country": "US", "event_type": "purchase", "amount": 100},
            {"id": 2, "country": "US", "event_type": "purchase", "amount": 50},
            {"id": 3, "country": "US", "event_type": "view", "amount": 0},
            {"id": 4, "country": "IN", "event_type": "purchase", "amount": 40},
            {"id": 5, "country": "IN", "event_type": "purchase", "amount": 60},
        ]

        rows, _ = run_steps(
            test_data,
            [
                {
                    "type": "aggregate",
                    "config": {
                        "groupBy": ["country", "event_type"],
                        "aggregations": [
                            {"column": "amount", "op": "sum", "as": "total"},
                            {"column": "id", "op": "count", "as": "event_count"},
                        ],
                    },
                }
            ],
        )
        # 3 groups: (US, purchase), (US, view), (IN, purchase)
        assert len(rows) == 3

        by_group = {(r["country"], r["event_type"]): r for r in rows}
        
        # US-purchase: 100 + 50 = 150, 2 events
        assert by_group[("US", "purchase")]["total"] == 150
        assert by_group[("US", "purchase")]["event_count"] == 2

        # US-view: 0, 1 event
        assert by_group[("US", "view")]["total"] == 0
        assert by_group[("US", "view")]["event_count"] == 1

        # IN-purchase: 40 + 60 = 100, 2 events
        assert by_group[("IN", "purchase")]["total"] == 100
        assert by_group[("IN", "purchase")]["event_count"] == 2


class TestAggregateRunnerWithFilters:
    """Tests for aggregate operator in pipelines with filters."""

    def test_filter_then_aggregate(self):
        """Test pipeline: filter → aggregate."""
        rows, step_stats = run_steps(
            EVENTS,
            [
                {
                    "type": "filter",
                    "config": {"column": "amount", "op": "gt", "value": 0},
                },
                {
                    "type": "aggregate",
                    "config": {
                        "groupBy": ["country"],
                        "aggregations": [
                            {"column": "amount", "op": "sum", "as": "total"},
                            {"column": "id", "op": "count", "as": "purchase_count"},
                        ],
                    },
                },
            ],
        )
        # After filter: 6 rows (removes 2 view events with amount=0)
        # After aggregate: 3 countries
        assert len(rows) == 3
        assert len(step_stats) == 2
        assert step_stats[0] == {"step": "0:filter", "rows_out": 6}
        assert step_stats[1] == {"step": "1:aggregate", "rows_out": 3}

        by_country = {r["country"]: r for r in rows}
        # US: 120 + 80 - 30 = 170 (3 purchase events)
        assert by_country["US"]["total"] == 170
        assert by_country["US"]["purchase_count"] == 3

    def test_filter_aggregate_select_pipeline(self):
        """Test full pipeline: filter → aggregate → select."""
        rows, step_stats = run_steps(
            EVENTS,
            [
                {
                    "type": "filter",
                    "config": {"column": "event_type", "op": "eq", "value": "purchase"},
                },
                {
                    "type": "aggregate",
                    "config": {
                        "groupBy": ["country"],
                        "aggregations": [
                            {"column": "amount", "op": "sum", "as": "total_amount"},
                            {"column": "id", "op": "count", "as": "purchase_count"},
                        ],
                    },
                },
                {
                    "type": "select",
                    "config": {"columns": ["country", "total_amount"]},
                },
            ],
        )
        # After filter: 5 purchase events
        # After aggregate: 3 groups
        # After select: 3 rows with only country and total_amount
        assert len(rows) == 3
        assert all(set(r.keys()) == {"country", "total_amount"} for r in rows)
        assert len(step_stats) == 3
        assert step_stats[0] == {"step": "0:filter", "rows_out": 5}
        assert step_stats[1] == {"step": "1:aggregate", "rows_out": 3}
        assert step_stats[2] == {"step": "2:select", "rows_out": 3}


class TestAggregateRunnerEdgeCases:
    """Tests for edge cases in aggregate operator."""

    def test_aggregate_empty_input(self):
        """Test aggregate with empty input."""
        rows, step_stats = run_steps(
            [],
            [
                {
                    "type": "aggregate",
                    "config": {
                        "groupBy": ["country"],
                        "aggregations": [{"column": "amount", "op": "sum", "as": "total"}],
                    },
                }
            ],
        )
        assert len(rows) == 0
        assert step_stats[0] == {"step": "0:aggregate", "rows_out": 0}

    def test_aggregate_single_row(self):
        """Test aggregate with single row input."""
        rows, _ = run_steps(
            [{"id": 1, "country": "US", "amount": 100}],
            [
                {
                    "type": "aggregate",
                    "config": {
                        "groupBy": ["country"],
                        "aggregations": [
                            {"column": "amount", "op": "sum", "as": "total"},
                            {"column": "id", "op": "count", "as": "count"},
                        ],
                    },
                }
            ],
        )
        assert len(rows) == 1
        assert rows[0] == {"country": "US", "total": 100, "count": 1}

    def test_aggregate_with_null_values(self):
        """Test aggregate correctly handles null values."""
        test_data = [
            {"id": 1, "country": "US", "amount": 100},
            {"id": 2, "country": "US", "amount": None},
            {"id": 3, "country": "US", "amount": 50},
        ]
        rows, _ = run_steps(
            test_data,
            [
                {
                    "type": "aggregate",
                    "config": {
                        "groupBy": ["country"],
                        "aggregations": [
                            {"column": "amount", "op": "sum", "as": "total"},
                            {"column": "amount", "op": "avg", "as": "average"},
                            {"column": "id", "op": "count", "as": "count"},
                        ],
                    },
                }
            ],
        )
        assert len(rows) == 1
        assert rows[0]["total"] == 150  # sum ignores nulls
        assert rows[0]["average"] == 75  # avg: (100 + 50) / 2
        assert rows[0]["count"] == 3  # count includes nulls
