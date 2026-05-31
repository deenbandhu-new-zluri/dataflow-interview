# DataFlow

A mini data-pipeline platform. You define **pipelines** that read rows from a
**source**, pass them through an ordered list of transform **operators**, and
produce an output. A **runner** executes pipelines and records each **run**.

```
source ──▶ operator ──▶ operator ──▶ … ──▶ output
            (filter)     (select)
```

- **Source data** lives in **S3** — each source is a JSON object in a bucket
  (`app/sources.py`).
- **Postgres** is the platform's **book-keeping** store: the pipelines users
  define and the full history of runs (`app/store.py`).

## Quick start

Bring up Postgres for book-keeping (schema is created on first boot):

```bash
docker compose up -d db
```

Configure S3 (the app auto-loads a local, gitignored `.env`):

```bash
cp .env.example .env          # fill in S3_BUCKET, creds, etc.
./scripts/seed_s3.sh          # uploads seed/events.json, seed/users.json
```

Credentials resolve through the standard AWS chain, so `AWS_PROFILE` / SSO work
too — `.env` is just the convenient default.

Then run the app:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python -m app.main        # dev server on http://127.0.0.1:8000  (docs at /docs)
pytest                    # unit tests; integration tests run if DB + S3 are reachable
```

## Try it

```bash
# What operators and sources exist?
curl localhost:8000/operators
curl localhost:8000/sources

# Create a pipeline: US events, projected to (user_id, amount)
curl -XPOST localhost:8000/pipelines -H 'content-type: application/json' -d '{
  "name": "us-events",
  "source": "events",
  "steps": [
    {"type": "filter", "config": {"column": "country", "op": "eq", "value": "US"}},
    {"type": "select", "config": {"columns": ["user_id", "amount"]}}
  ]
}'

# Run it (use the id returned above). The run is persisted to Postgres.
curl -XPOST localhost:8000/pipelines/1/run
curl localhost:8000/runs/1
```

## Layout

| Path | Responsibility |
|------|----------------|
| `app/sources.py`        | Source connectors — read named datasets (`events`, `users`) from S3. |
| `app/operators.py`      | Transform operators: `validate_step` and `apply_step`. |
| `app/engine/runner.py`  | Executes a pipeline: load source → fold operators → stamp the run. |
| `app/store.py`          | Postgres-backed persistence for pipelines and runs (book-keeping). |
| `app/db.py`             | Postgres pool. `app/config.py` reads DB + S3 settings from env. |
| `app/api.py`            | FastAPI HTTP layer + error → status-code mapping. |
| `db/schema.sql`         | Book-keeping schema (`pipelines`, `runs`), loaded on DB first boot. |
| `seed/`, `scripts/`     | Source datasets + `seed_s3.sh` to upload them to your bucket. |
| `tests/`                | Unit tests (no deps) + `tests/integration/` (needs Postgres + S3). |

## How an operator works

Operators live in `app/operators.py`. A pipeline step is
`{"type": "...", "config": {...}}`. Two functions act on a step:

- `validate_step(step)` — raise `ValidationError` if the config is malformed
  (called when a pipeline is created)
- `apply_step(rows, step)` — transform rows in, rows out (called by the runner)

`GET /operators` reports the available operator types. `filter` and `select`
are implemented today.
