"""HTTP API for the DataFlow platform."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .errors import NotFoundError, ValidationError
from .engine.runner import execute
from .operators import OPERATOR_TYPES, validate_step
from .sources import source_names
from .store import store

app = FastAPI(title="DataFlow", description="A mini data-pipeline platform")


# --- request models --------------------------------------------------------


class Step(BaseModel):
    type: str
    config: dict = Field(default_factory=dict)


class PipelineCreate(BaseModel):
    name: str
    source: str
    steps: list[Step]


# --- error handling --------------------------------------------------------


@app.exception_handler(ValidationError)
def _on_validation_error(_: Request, exc: ValidationError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"error": str(exc)})


@app.exception_handler(NotFoundError)
def _on_not_found_error(_: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"error": str(exc)})


# --- discovery -------------------------------------------------------------


@app.get("/operators")
def list_operators() -> dict:
    return {"operators": OPERATOR_TYPES}


@app.get("/sources")
def list_sources() -> dict:
    return {"sources": source_names()}


# --- pipelines -------------------------------------------------------------


@app.post("/pipelines", status_code=201)
def create_pipeline(body: PipelineCreate) -> dict:
    # Validate every step before persisting the pipeline, so a stored pipeline
    # is always runnable.
    steps = [step.model_dump() for step in body.steps]
    for step in steps:
        validate_step(step)
    return store.create_pipeline(body.name, body.source, steps)


@app.get("/pipelines")
def list_pipelines() -> dict:
    return {"pipelines": store.list_pipelines()}


@app.get("/pipelines/{pipeline_id}")
def get_pipeline(pipeline_id: int) -> dict:
    return store.get_pipeline(pipeline_id)


@app.post("/pipelines/{pipeline_id}/run")
def run_pipeline(pipeline_id: int) -> dict:
    pipeline = store.get_pipeline(pipeline_id)
    result = execute(pipeline)
    return store.create_run(pipeline_id, result)


# --- runs ------------------------------------------------------------------


@app.get("/runs/{run_id}")
def get_run(run_id: int) -> dict:
    return store.get_run(run_id)
