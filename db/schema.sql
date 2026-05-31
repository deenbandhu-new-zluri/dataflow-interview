-- Book-keeping schema for the DataFlow platform.
-- Mounted into the postgres container's init dir, so it runs once on first boot.
--
-- Postgres stores platform metadata only: the pipelines users define and the
-- history of runs. Source datasets live in the application (see app/sources.py).

CREATE TABLE pipelines (
    id         SERIAL PRIMARY KEY,
    name       TEXT        NOT NULL,
    source     TEXT        NOT NULL,
    steps      JSONB       NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE runs (
    id          SERIAL PRIMARY KEY,
    pipeline_id INTEGER     NOT NULL REFERENCES pipelines(id),
    status      TEXT        NOT NULL,
    started_at  TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ NOT NULL,
    row_count   INTEGER     NOT NULL,
    step_stats  JSONB       NOT NULL,
    output      JSONB       NOT NULL
);
