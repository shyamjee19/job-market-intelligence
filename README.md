# job-market-intelligence

A multi-source data pipeline that pulls job postings from several APIs, validates and cleans them, models them in a Postgres star schema, and serves them through a FastAPI backend and a React dashboard.

## Architecture

```
RemoteOK API  ─┐
Arbeitnow API ─┼─> collector (Bronze: data/raw/<source>/*.json)
(pluggable)   ─┘        │
                         v
              validate -> transform -> load  (etl/)
                         │
                         v
      Postgres star schema (Fact_Jobs + Dim_Company/Location/Skill/Date/Source)
                         │
                         v
              FastAPI (api/) --> React UI (frontend/)
```

- **collector/sources/** is a pluggable source registry. Each source (`RemoteOKSource`, `ArbeitnowSource`, ...) implements one `fetch()` method returning raw records exactly as its API responds. Adding a new source (Adzuna, Jooble, USAJobs, Kaggle, ...) means: add its URL/key to `config/settings.py`, implement `JobSource` in `collector/sources/`, register it in `collector/sources/registry.py`, and add a normalizer in `etl/transform.py` - nothing else in the pipeline changes.
- **etl/validate.py** schema-checks each raw record before it's normalized (required fields per source). Records that fail are logged to the `rejected_records` table with their reasons, not silently dropped.
- **etl/transform.py** normalizes each source's raw shape into one common schema, then deduplicates by `external_id`.
- **database/schema.sql** is a proper star schema: `fact_jobs` (one row per posting per source, unique on `(source_key, external_id)`) plus `dim_company`, `dim_location`, `dim_skill`, `dim_date`, `dim_source`, and a `bridge_job_skill` many-to-many table. `repository.py` (the ETL write path) does get-or-create dimension resolution and upserts the fact row; `queries.py` (the API read path) joins them back for the UI.
- **api/** is a FastAPI app: job search/filter/pagination, job detail, companies, skills, market stats (summary, top companies, top skills by category, postings over time, salary distribution, source breakdown, world hiring map, day-over-day trend), and CSV export.
- **frontend/** is a React + Vite + TypeScript app: a searchable/filterable job list (with a source filter and CSV export), a job detail view, and a stats dashboard - dark mode, skeleton loading states, a world hiring map (D3 + topojson, no API key needed), and charts built to the project's data-viz conventions.
- **utils/geo.py** and **utils/skill_categories.py** are best-effort, keyword/lookup-table classifiers (no external geocoding or ML): `geo.py` infers a country from free-text location strings for the map; `skill_categories.py` buckets tags into AI/Cloud/Tech for the dashboard's skills breakdown. Both are intentionally approximate - see their docstrings for what they miss.
- **Hybrid work-mode detection** is keyword-based (`utils.helper.detect_remote_type` scans title/description for "hybrid"), since neither source reports it as a structured field.

### Future extension: streaming stack, more sources, cloud warehouse

- `kafka/`, `spark/`, `snowflake/`, and `docker/airflow/` contain a Kafka -> Spark -> Snowflake -> Airflow pipeline that's scaffolded but **not wired into the active pipeline** (see `docker/docker-compose.full-stack.yml.example`). Documented future path for scaling beyond direct Python -> Postgres.
- Adzuna, Jooble, USAJobs, and Kaggle are not yet integrated - `config/settings.py` already has placeholder env vars for their credentials, so wiring one in is a config + one new `JobSource` class, not a redesign.
- Snowflake credentials go in `.env` (`SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_PASSWORD`, ...); `snowflake/load_to_snowflake.py` is the existing loader, currently pointed at the old Parquet-based flow and not yet updated for the new star schema.
- An AI assistant (skill-trend Q&A, resume suggestions) needs an LLM API key and hasn't been built yet.

## Setup

1. **Start Postgres.** This project has been developed against a local Postgres instance (not Docker) - if you have one running already, skip to step 2. Otherwise: `docker compose up -d` (requires Docker Desktop).
2. **Create a virtualenv and install Python dependencies:**
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Configure environment:** copy `.env.example` to `.env` and adjust if needed.
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
python main.py run                  # collect every registered source, then transform + load
python main.py run --source arbeitnow   # just one source
python main.py collect              # fetch only, save raw snapshots
python main.py etl                  # transform + load the latest raw snapshots
```

Registered sources live in `collector/sources/registry.py` - currently `remoteok` and `arbeitnow`.

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

Unit tests (`test_helper.py`, `test_validate.py`, `test_transform.py`, `test_geo.py`, `test_skill_categories.py`) run with no dependencies. Integration tests (`test_connection.py`, `test_repository.py`, `test_api.py`) need a reachable Postgres instance and skip automatically if one isn't available. `test_repository.py` and `test_connection.py` run against an isolated `{DB_NAME}_test` database (auto-provisioned), never your real data.

## Project layout

```
collector/           sources/ (pluggable JobSource per API), retry logic, raw snapshot writer
config/               settings.py (env-backed) and constants.py
database/             schema.sql (star schema), connection.py, repository.py (writes), queries.py (reads)
etl/                  extract.py, validate.py, transform.py, load.py, pipeline.py
api/                  FastAPI app: main.py, schemas.py
frontend/             React + Vite + TypeScript UI (src/pages, src/components, src/api)
utils/                logger.py, helper.py, exceptions.py, geo.py (country inference), skill_categories.py
tests/                unit + integration tests
data/raw/<source>/    raw JSON snapshots per source (gitignored)
data/processed/       reserved for the future Spark stage
logs/                 application log file (gitignored)
```
