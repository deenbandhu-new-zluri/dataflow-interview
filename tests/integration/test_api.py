"""End-to-end API tests that exercise the Postgres book-keeping layer and the
S3-backed sources.

These are skipped unless both backing services are reachable, e.g. after:

    docker compose up -d db s3
"""

import psycopg
import pytest
from fastapi.testclient import TestClient

from app.api import app
from app.config import DATABASE_URL
from app.sources import get_source


def _deps_reachable() -> bool:
    try:
        with psycopg.connect(DATABASE_URL, connect_timeout=2):
            pass
        get_source("events").read()  # confirms S3 + seed data
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _deps_reachable(), reason="Postgres/S3 not reachable")


@pytest.fixture()
def client():
    return TestClient(app)


def test_create_run_and_fetch_pipeline(client):
    body = {
        "name": "us-purchases",
        "source": "events",
        "steps": [
            {"type": "filter", "config": {"column": "country", "op": "eq", "value": "US"}},
        ],
    }
    created = client.post("/pipelines", json=body)
    assert created.status_code == 201
    pipeline_id = created.json()["id"]

    run = client.post(f"/pipelines/{pipeline_id}/run")
    assert run.status_code == 200
    assert run.json()["row_count"] == 4
    assert run.json()["status"] == "success"

    # The run is persisted and refetchable by id.
    run_id = run.json()["id"]
    fetched = client.get(f"/runs/{run_id}")
    assert fetched.status_code == 200
    assert fetched.json()["pipeline_id"] == pipeline_id


def test_invalid_step_config_is_rejected(client):
    body = {
        "name": "bad",
        "source": "events",
        "steps": [{"type": "filter", "config": {"op": "eq"}}],
    }
    resp = client.post("/pipelines", json=body)
    assert resp.status_code == 400
    assert "column" in resp.json()["error"]


def test_unknown_pipeline_is_404(client):
    assert client.get("/pipelines/999999").status_code == 404
