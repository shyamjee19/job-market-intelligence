# job-market-intelligence

A small data pipeline that pulls remote job postings from the [RemoteOK API](https://remoteok.com/api), cleans them, loads them into Postgres, and serves them through a FastAPI backend and a React dashboard.

## Architecture

```
RemoteOK API --> collector --> data/raw/jobs_*.json --> etl (extract/transform/load) --> Postgres --> FastAPI (api/) --> React UI (frontend/)
```

- **collector/** fetches the current job feed and writes an immutable, timestamped JSON snapshot to `data/raw/` (plus a `jobs_latest.json` pointer). Retries on transient failures.
- **etl/** reads the latest raw snapshot, cleans/validates/deduplicates records, and upserts them into Postgres keyed on `job_id` (re-running the pipeline updates existing postings instead of duplicating them).
- **database/** owns the schema, the write path (`repository.py`, used by ETL), and the read path (`queries.py`, used by the API).
- **config/** and **utils/** hold shared settings, logging, and pure helper functions.
- **api/** is a FastAPI app serving job listings and market stats over `/api/*`.
- **frontend/** is a React + Vite + TypeScript app: a searchable job list, a job detail view, and a stats dashboard.

### Future extension: streaming stack

`kafka/`, `spark/`, `snowflake/`, and `docker/airflow/` contain a more advanced Kafka -> Spark -> Snowflake -> Airflow pipeline that was scaffolded but is **not** part of the active pipeline right now (see `docker/docker-compose.full-stack.yml.example`). It's kept as a documented future path for when this needs to scale beyond a single Postgres instance - it isn't wired up and doesn't need to run for local development.

## Setup

1. **Start Postgres:**
   ```
   docker compose up -d
   ```
2. **Create a virtualenv and install Python dependencies:**
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Configure environment:** copy `.env.example` to `.env` and adjust if needed (defaults match `docker-compose.yml`).
4. **Initialize the schema:**
   ```
   python main.py init-db
   ```
5. **Install frontend dependencies:**
   ```
   cd frontend
   npm install
   ```
   Copy `frontend/.env.example` to `frontend/.env` if you need to point it at a non-default API URL.

## Running the pipeline

```
python main.py run       # collect from the API, then transform + load
python main.py collect   # fetch only, save raw snapshot
python main.py etl       # transform + load the latest raw snapshot
```

## Running the UI

In two terminals, from the repo root:

```
.venv\Scripts\python.exe -m uvicorn api.main:app --reload --port 8000
```

```
cd frontend
npm run dev
```

Then open http://localhost:5173. The API serves on http://localhost:8000 (interactive docs at `/docs`).

## Tests

```
pytest
```

Unit tests (`test_helper.py`, `test_transform.py`) run with no dependencies. Integration tests (`test_connection.py`, `test_repository.py`, `test_api.py`) need a reachable Postgres instance and skip automatically if one isn't available. `test_repository.py` and `test_connection.py` run against an isolated `{DB_NAME}_test` database (auto-provisioned), never your real data.

## Project layout

```
collector/   API client + retry logic + raw snapshot writer
config/      settings.py (env-backed) and constants.py
database/    schema.sql, connection.py, repository.py (writes), queries.py (reads)
etl/         extract.py, transform.py, load.py, pipeline.py
api/         FastAPI app: main.py, schemas.py
frontend/    React + Vite + TypeScript UI (src/pages, src/components, src/api)
utils/       logger.py, helper.py, exceptions.py
tests/       unit + integration tests
data/raw/    raw JSON snapshots (gitignored)
data/processed/  reserved for the future Spark stage
logs/        application log file (gitignored)
```
