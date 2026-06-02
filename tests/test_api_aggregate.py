"""API integration tests for aggregate operator.

Tests the aggregate operator through the HTTP API layer,
similar to filter and select tests.
"""

import pytest
from fastapi.testclient import TestClient

from app.api import app

client = TestClient(app)


class TestAggregateAPIBasic:
    """Basic aggregate operator tests via API."""

    def test_aggregate_operator_listed(self):
        """Test that aggregate operator is listed in /operators."""
        response = client.get("/operators")
        assert response.status_code == 200
        data = response.json()
        assert "aggregate" in data["operators"]

    def test_create_pipeline_with_aggregate(self):
        """Test creating a pipeline with aggregate operator."""
        response = client.post(
            "/pipelines",
            json={
                "name": "sales-by-country",
                "source": "events",
                "steps": [
                    {
                        "type": "aggregate",
                        "config": {
                            "groupBy": ["country"],
                            "aggregations": [
                                {"column": "amount", "op": "sum", "as": "total_amount"},
                                {"column": "id", "op": "count", "as": "events"},
                            ],
                        },
                    }
                ],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "sales-by-country"
        assert data["source"] == "events"
        assert len(data["steps"]) == 1
        assert data["steps"][0]["type"] == "aggregate"

    def test_aggregate_validation_missing_groupby(self):
        """Test validation: missing groupBy field."""
        response = client.post(
            "/pipelines",
            json={
                "name": "invalid-aggregate",
                "source": "events",
                "steps": [
                    {
                        "type": "aggregate",
                        "config": {
                            "aggregations": [{"column": "amount", "op": "sum", "as": "total"}]
                        },
                    }
                ],
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert "groupBy" in data["error"]

    def test_aggregate_validation_empty_groupby(self):
        """Test validation: empty groupBy list."""
        response = client.post(
            "/pipelines",
            json={
                "name": "invalid-aggregate",
                "source": "events",
                "steps": [
                    {
                        "type": "aggregate",
                        "config": {
                            "groupBy": [],
                            "aggregations": [{"column": "amount", "op": "sum", "as": "total"}],
                        },
                    }
                ],
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert "groupBy" in data["error"] and "empty" in data["error"].lower()

    def test_aggregate_validation_missing_aggregations(self):
        """Test validation: missing aggregations field."""
        response = client.post(
            "/pipelines",
            json={
                "name": "invalid-aggregate",
                "source": "events",
                "steps": [{"type": "aggregate", "config": {"groupBy": ["country"]}}],
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert "aggregations" in data["error"]

    def test_aggregate_validation_empty_aggregations(self):
        """Test validation: empty aggregations list."""
        response = client.post(
            "/pipelines",
            json={
                "name": "invalid-aggregate",
                "source": "events",
                "steps": [
                    {
                        "type": "aggregate",
                        "config": {"groupBy": ["country"], "aggregations": []},
                    }
                ],
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert "aggregations" in data["error"] and "empty" in data["error"].lower()

    def test_aggregate_validation_invalid_op(self):
        """Test validation: invalid aggregation operation."""
        response = client.post(
            "/pipelines",
            json={
                "name": "invalid-aggregate",
                "source": "events",
                "steps": [
                    {
                        "type": "aggregate",
                        "config": {
                            "groupBy": ["country"],
                            "aggregations": [{"column": "amount", "op": "median", "as": "result"}],
                        },
                    }
                ],
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert "op" in data["error"]

    def test_aggregate_validation_missing_column(self):
        """Test validation: missing column in aggregation."""
        response = client.post(
            "/pipelines",
            json={
                "name": "invalid-aggregate",
                "source": "events",
                "steps": [
                    {
                        "type": "aggregate",
                        "config": {
                            "groupBy": ["country"],
                            "aggregations": [{"op": "sum", "as": "total"}],
                        },
                    }
                ],
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert "column" in data["error"]

    def test_aggregate_validation_missing_as(self):
        """Test validation: missing 'as' field in aggregation."""
        response = client.post(
            "/pipelines",
            json={
                "name": "invalid-aggregate",
                "source": "events",
                "steps": [
                    {
                        "type": "aggregate",
                        "config": {
                            "groupBy": ["country"],
                            "aggregations": [{"column": "amount", "op": "sum"}],
                        },
                    }
                ],
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert "as" in data["error"]


@pytest.mark.integration
class TestAggregateAPIExecution:
    """Integration tests for aggregate execution via API.
    
    Requires: Postgres and S3 to be available.
    """

    def test_execute_aggregate_pipeline_single_groupby(self):
        """Test executing aggregate pipeline with single groupBy."""
        # Create pipeline
        create_response = client.post(
            "/pipelines",
            json={
                "name": "test-aggregate-single-groupby",
                "source": "events",
                "steps": [
                    {
                        "type": "aggregate",
                        "config": {
                            "groupBy": ["country"],
                            "aggregations": [
                                {"column": "amount", "op": "sum", "as": "total_amount"},
                                {"column": "id", "op": "count", "as": "events"},
                            ],
                        },
                    }
                ],
            },
        )
        assert create_response.status_code == 201
        pipeline_id = create_response.json()["id"]

        # Run pipeline
        run_response = client.post(f"/pipelines/{pipeline_id}/run")
        assert run_response.status_code == 200
        run_data = run_response.json()
        assert run_data["status"] == "success"
        
        # Verify output
        output = run_data["output"]
        assert len(output) == 3  # US, IN, DE
        
        # Find and verify US group
        us_group = next((r for r in output if r["country"] == "US"), None)
        assert us_group is not None
        assert us_group["total_amount"] == 170
        assert us_group["events"] == 4
        
        # Find and verify IN group
        in_group = next((r for r in output if r["country"] == "IN"), None)
        assert in_group is not None
        assert in_group["total_amount"] == 100
        assert in_group["events"] == 3
        
        # Find and verify DE group
        de_group = next((r for r in output if r["country"] == "DE"), None)
        assert de_group is not None
        assert de_group["total_amount"] == 200
        assert de_group["events"] == 1

    def test_execute_aggregate_pipeline_multiple_groupby(self):
        """Test executing aggregate with multiple groupBy columns."""
        create_response = client.post(
            "/pipelines",
            json={
                "name": "test-aggregate-multi-groupby",
                "source": "events",
                "steps": [
                    {
                        "type": "aggregate",
                        "config": {
                            "groupBy": ["country", "event_type"],
                            "aggregations": [
                                {"column": "amount", "op": "sum", "as": "total_amount"},
                                {"column": "id", "op": "count", "as": "event_count"},
                            ],
                        },
                    }
                ],
            },
        )
        assert create_response.status_code == 201
        pipeline_id = create_response.json()["id"]

        run_response = client.post(f"/pipelines/{pipeline_id}/run")
        assert run_response.status_code == 200
        run_data = run_response.json()
        assert run_data["status"] == "success"
        
        output = run_data["output"]
        # Should have multiple groups based on country and event_type combinations
        assert len(output) > 3

    def test_execute_filter_aggregate_pipeline(self):
        """Test filter → aggregate pipeline."""
        create_response = client.post(
            "/pipelines",
            json={
                "name": "test-filter-aggregate",
                "source": "events",
                "steps": [
                    {"type": "filter", "config": {"column": "amount", "op": "gt", "value": 0}},
                    {
                        "type": "aggregate",
                        "config": {
                            "groupBy": ["country"],
                            "aggregations": [
                                {"column": "amount", "op": "sum", "as": "total"},
                                {"column": "amount", "op": "count", "as": "count"},
                            ],
                        },
                    },
                ],
            },
        )
        assert create_response.status_code == 201
        pipeline_id = create_response.json()["id"]

        run_response = client.post(f"/pipelines/{pipeline_id}/run")
        assert run_response.status_code == 200
        run_data = run_response.json()
        
        # Verify step stats
        step_stats = run_data["step_stats"]
        assert len(step_stats) >= 3  # source + filter + aggregate
        assert "filter" in step_stats[1]["step"]
        assert "aggregate" in step_stats[2]["step"]
        
        # After filter: 6 rows (removes 2 view events with amount=0)
        # After aggregate: 3 countries
        assert step_stats[2]["rows_out"] == 3

    def test_execute_all_aggregation_operations(self):
        """Test all aggregation operations: sum, count, avg, min, max."""
        create_response = client.post(
            "/pipelines",
            json={
                "name": "test-all-agg-ops",
                "source": "events",
                "steps": [
                    {
                        "type": "aggregate",
                        "config": {
                            "groupBy": ["country"],
                            "aggregations": [
                                {"column": "amount", "op": "sum", "as": "total"},
                                {"column": "amount", "op": "count", "as": "count"},
                                {"column": "amount", "op": "avg", "as": "average"},
                                {"column": "amount", "op": "min", "as": "minimum"},
                                {"column": "amount", "op": "max", "as": "maximum"},
                            ],
                        },
                    }
                ],
            },
        )
        assert create_response.status_code == 201
        pipeline_id = create_response.json()["id"]

        run_response = client.post(f"/pipelines/{pipeline_id}/run")
        assert run_response.status_code == 200
        run_data = run_response.json()
        
        output = run_data["output"]
        # US group
        us = next((r for r in output if r["country"] == "US"), None)
        assert us is not None
        assert us["total"] == 170
        assert us["count"] == 4
        assert us["average"] == 42.5
        assert us["minimum"] == -30
        assert us["maximum"] == 120

    def test_execute_aggregate_select_pipeline(self):
        """Test aggregate → select pipeline."""
        create_response = client.post(
            "/pipelines",
            json={
                "name": "test-aggregate-select",
                "source": "events",
                "steps": [
                    {
                        "type": "aggregate",
                        "config": {
                            "groupBy": ["country"],
                            "aggregations": [
                                {"column": "amount", "op": "sum", "as": "total"},
                                {"column": "amount", "op": "avg", "as": "average"},
                            ],
                        },
                    },
                    {"type": "select", "config": {"columns": ["country", "total"]}},
                ],
            },
        )
        assert create_response.status_code == 201
        pipeline_id = create_response.json()["id"]

        run_response = client.post(f"/pipelines/{pipeline_id}/run")
        assert run_response.status_code == 200
        run_data = run_response.json()
        
        output = run_data["output"]
        # After select, should only have country and total
        for row in output:
            assert set(row.keys()) == {"country", "total"}

    def test_get_run_with_aggregate_output(self):
        """Test fetching run result with aggregate output."""
        # Create and run pipeline
        create_response = client.post(
            "/pipelines",
            json={
                "name": "test-get-run",
                "source": "events",
                "steps": [
                    {
                        "type": "aggregate",
                        "config": {
                            "groupBy": ["country"],
                            "aggregations": [{"column": "amount", "op": "sum", "as": "total"}],
                        },
                    }
                ],
            },
        )
        pipeline_id = create_response.json()["id"]

        run_response = client.post(f"/pipelines/{pipeline_id}/run")
        run_id = run_response.json()["id"]

        # Get run
        get_response = client.get(f"/runs/{run_id}")
        assert get_response.status_code == 200
        run_data = get_response.json()
        
        assert run_data["status"] == "success"
        assert run_data["row_count"] == 3
        assert len(run_data["output"]) == 3
        assert len(run_data["step_stats"]) >= 2
