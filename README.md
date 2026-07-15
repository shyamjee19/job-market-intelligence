# job-market-intelligence

A multi-source data pipeline that pulls job postings from several APIs, validates and cleans them, models them in a Postgres star schema, and serves them through a FastAPI backend, a React dashboard, and a RAG-grounded AI assistant.

## Architecture

```
RemoteOK API  ─┐
Arbeitnow API ─┤
Adzuna API    ─┼─> collector (Bronze: data/raw/<source>/*.json)
USAJobs API   ─┘        │
(pluggable)              v
              validate -> transform -> load  (etl/)
                         │
                         v
      Postgres star schema (Fact_Jobs + Dim_Company/Location/Skill/Date/Source)
                         │
                         v
              FastAPI (api/) --> React UI (frontend/)
```

- **collector/sources/** is a pluggable source registry. Each source (`RemoteOKSource`, `ArbeitnowSource`, `AdzunaSource`, `USAJobsSource`) implements one `fetch()` method returning raw records exactly as its API responds. Adding another (Jooble, Kaggle, ...) means: add its URL/key to `config/settings.py`, implement `JobSource` in `collector/sources/`, register it in `collector/sources/registry.py`, and add a normalizer in `etl/transform.py` - nothing else in the pipeline changes.
- **Credential-gated sources activate automatically.** RemoteOK and Arbeitnow need no key and are always on. Adzuna and USAJobs are fully wired (fetch, validation, normalization) but `collector/sources/registry.py` only adds them to the active `SOURCES` registry once their required `.env` settings are all present - an empty `.env` means they're silently skipped on every `run`/`collect`/`etl` rather than failing. Requesting one explicitly (`--source adzuna`) without credentials raises a clear error naming exactly which env vars are missing, instead of a raw 401.
- **USAJobs is live-verified**: built against its documented API contract, then confirmed end-to-end with real credentials (250 real federal postings collected, validated, and loaded with zero rejections). **Adzuna is still built against documentation only** - unit-tested against realistic sample fixtures, but not yet exercised against the live API (no credentials yet) - worth a smoke test the first time real keys go in `.env`.
- **etl/validate.py** schema-checks each raw record before it's normalized (required fields per source). Records that fail are logged to the `rejected_records` table with their reasons, not silently dropped.
- **etl/transform.py** normalizes each source's raw shape into one common schema, then deduplicates by `external_id`.
- **database/schema.sql** is a proper star schema: `fact_jobs` (one row per posting per source, unique on `(source_key, external_id)`) plus `dim_company`, `dim_location`, `dim_skill`, `dim_date`, `dim_source`, and a `bridge_job_skill` many-to-many table. `repository.py` (the ETL write path) does get-or-create dimension resolution and upserts the fact row; `queries.py` (the API read path) joins them back for the UI.
- **api/** is a FastAPI app: job search/filter/pagination, job detail, companies, skills, market stats (summary, top companies, top skills by category, postings over time, salary distribution, source breakdown, world hiring map, day-over-day trend), and CSV export.
- **frontend/** is a React + Vite + TypeScript app: a searchable/filterable job list (with a source filter and CSV export), a job detail view, and a stats dashboard - dark mode, skeleton loading states, a world hiring map (D3 + topojson, no API key needed), and charts built to the project's data-viz conventions.
- **utils/geo.py** and **utils/skill_categories.py** are best-effort, keyword/lookup-table classifiers (no external geocoding or ML): `geo.py` infers a country from free-text location strings for the map; `skill_categories.py` buckets tags into AI/Cloud/Tech for the dashboard's skills breakdown. Both are intentionally approximate - see their docstrings for what they miss.
- **Hybrid work-mode detection** is keyword-based (`utils.helper.detect_remote_type` scans title/description for "hybrid"), since neither source reports it as a structured field.

### AI module (`ai/`)

A RAG (Retrieval-Augmented Generation) chatbot that answers questions about the job market grounded in the actual postings in Postgres - not the LLM's training data. Every answer cites the specific postings (company + position) it drew on, so it's checkable rather than trusted blindly.

```
User question
     │
     v
ai/router.py  (POST /api/ai/chat - rate limiting, input validation)
     │
     v
ai/services/rag_chatbot_service.py
     │
     ├─> embed question  ──> ai/providers/  (OpenAI / Claude / Azure OpenAI / Ollama)
     │
     ├─> retrieve similar postings ──> ai/vectorstore/  (in-memory default / Pinecone)
     │
     └─> build grounded prompt ──> ai/prompts/rag_chatbot.py ──> chat provider ──> cited answer
```

- **Everything is provider-agnostic by design.** `ai/providers/base.py` defines `ChatProvider` and `EmbeddingProvider` interfaces (separate, because Anthropic has no embeddings API); `ai/providers/registry.py` picks the active implementation from `AI_CHAT_PROVIDER` / `AI_EMBEDDING_PROVIDER` in `.env`. Adding a new provider is one class + one line in the registry - nothing in `ai/services/` changes.
- **OpenAI is the live, verified default.** Claude, Azure OpenAI, and Ollama are fully implemented against their documented APIs but unverified (no credentials/local install available while building them) - same "built to spec, not yet exercised live" status Adzuna had before its keys arrived.
- **The RAG chatbot works today with no paid vector database.** `ai/vectorstore/` has the same swappable-provider pattern: `InMemoryVectorStore` (numpy cosine similarity, persists to `data/ai/memory_vector_store.json`, no account needed) is the default, so the feature is fully testable right now. Set `VECTOR_STORE_PROVIDER=pinecone` once you have a Pinecone key and nothing else changes - `ai/services/rag_chatbot_service.py` codes only against the `VectorStore` interface.
- **Indexing is a separate, explicit step** (`python main.py ai-index`, or `ai/services/rag_indexer.py`) - it embeds every job posting and upserts it into the active vector store. Not automatic after `etl`, so re-embedding (and its API cost) only happens when you ask for it.
- **AI security**: input length limits (`AI_MAX_MESSAGE_LENGTH`), a sliding-window rate limiter per client IP (`AI_RATE_LIMIT_PER_MINUTE`, in-memory - dev-grade, would move to Redis for multi-worker deployments), in-memory conversation history (also dev-grade, same caveat), and prompt-injection resistance in the system prompt (the LLM is told retrieved job text is data to read, not instructions to follow). API keys only ever come from `.env` via `config/settings.py`, never hardcoded or logged; token usage is logged per request.
- **What's not built**: the other 12 AI features from the original spec (Resume Analyzer, Dashboard NL-to-SQL Assistant, Trend Prediction, Report Generator, Notifications, Interview Assistant, etc.) - each needs real infrastructure beyond an LLM call (file upload/parsing, a forecasting model, PDF generation, a notification delivery system) and was scoped out of this pass. The provider/vector-store architecture here is built to support them without a redesign when they're prioritized.

### SaaS platform layer (`auth/`, `jobs/`, `api/routes/users.py`, `api/routes/admin.py`)

Everything a user-facing product needs on top of the data platform: accounts, personalization, and admin operations - built against the real Postgres instance and versioned under `/api/v1`.

```
Browser
   │
   ├─> POST /api/v1/auth/register | /login        ──> bcrypt hash, JWT access + refresh pair
   ├─> GET  /api/v1/auth/google | /github          ──> OAuth2 authorization-code flow (CSRF state)
   │
   ├─> GET/PUT  /api/v1/users/me/profile           ──> headline, bio, skills, experience
   ├─> POST     /api/v1/users/me/resume            ──> extension + magic-byte validated upload
   ├─> GET/POST/DELETE /api/v1/users/me/saved-jobs
   ├─> GET/POST/DELETE /api/v1/users/me/favorites
   ├─> GET/POST/PATCH/DELETE /api/v1/users/me/alerts
   │
   └─> /api/v1/admin/*  (role=admin only)          ──> user list, role/active toggles, audit log, stats
```

- **JWT auth with refresh rotation.** `auth/security.py` issues short-lived access tokens (30 min default) and longer-lived refresh tokens (30 days default); `POST /auth/refresh` is single-use - each refresh token is revoked the moment it's exchanged and a new one issued, so a stolen, already-used refresh token is inert. Refresh tokens are stored server-side as SHA-256 hashes, never plaintext.
- **RBAC** is a `role` column (`user`/`admin`) on `users`, enforced via FastAPI dependencies (`auth/dependencies.py`): `get_current_user`, `require_admin`, `get_optional_user`. Because a JWT is immutable once signed, promoting a user to admin (see below) doesn't take effect until they log in again - their existing token still carries the old role.
- **Google and GitHub OAuth are fully implemented and inactive until configured** - same conditional-activation pattern as Adzuna/USAJobs/Pinecone. Without credentials in `.env`, `/auth/google` and `/auth/github` return a clear 503 instead of crashing; the login page's OAuth buttons work as soon as you add `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET` or `GITHUB_CLIENT_ID`/`GITHUB_CLIENT_SECRET`. The callback never puts a real JWT in the browser URL/history - it redirects with a one-time exchange code (`auth/oauth/state_store.py`) that the frontend swaps for tokens via `POST /auth/oauth/exchange`.
- **Resume upload is validated, not trusted.** `utils/resume_storage.py` checks the file extension (`.pdf`/`.doc`/`.docx`), size (`RESUME_MAX_SIZE_MB`), and the actual file signature (magic bytes) before saving - a renamed `.exe` won't pass. Files are stored under a per-user, UUID-named path, never the original filename, so there's no path-traversal or filename-collision risk.
- **Job alerts** (`jobs/alert_matcher.py`) match saved search criteria (keywords, location, tag, source, salary, remote type) against `fact_jobs` and use a high-water-mark (`last_notified_job_key`) so re-running never re-notifies the same posting twice. `check_all_alerts()` is plain Python, independently callable - `python main.py check-alerts` runs it with no broker needed. `jobs/celery_app.py` wraps the same function in an hourly Celery Beat schedule for production use once `REDIS_URL` is set.
- **Email is logged, not sent, by design for this pass.** `utils/email.py` writes the subject/body to the app log and the `notification_log` table instead of calling a real SMTP server, unless `SMTP_HOST` etc. are set in `.env` - so the alert pipeline is fully testable without an email account.
- **Caching (`utils/cache.py`)** is a small `Cache` interface with `InMemoryCache` (default) and `RedisCache` implementations, chosen once at startup by whether `REDIS_URL` is set. Stats endpoints are wrapped in a `@cached()` decorator; `RedisCache` serializes Postgres `Decimal`/`date` values via `json.dumps(..., default=str)` since FastAPI's response models coerce them back on the way out.
- **Rate limiting** (`utils/rate_limiter.py`) is a generic in-memory sliding-window limiter keyed by `(namespace, client_ip)`, shared by the auth endpoints (`AUTH_RATE_LIMIT_PER_MINUTE`) and the AI chat endpoint - same caveat as the AI module's limiter: dev-grade, would move to Redis for multi-worker deployments.
- **Audit logging** (`log_audit()` in `database/users_repository.py`) records register/login/profile-update/alert-create-style events with the acting user, action, resource, and IP - visible in the admin dashboard's audit log tab.
- **`/health` checks real dependencies, not just that the process is up** - it does a fresh DB query and (if `REDIS_URL` is set) a fresh Redis `PING` on every call, not a cached "was it up at startup" flag.
- **API versioning**: every route in this section is mounted under `/api/v1` (`api/main.py`); interactive docs are at `/docs`.

**Promoting a user to admin** (there's no self-service path, by design):
```sql
UPDATE users SET role = 'admin' WHERE email = 'you@example.com';
```
Then log out and back in - the new role only applies to a freshly issued token.

### Future extension: streaming stack, more sources, cloud warehouse

- `kafka/`, `spark/`, `snowflake/`, and `docker/airflow/` contain a Kafka -> Spark -> Snowflake -> Airflow pipeline that's scaffolded but **not wired into the active pipeline** (see `docker/docker-compose.full-stack.yml.example`). Documented future path for scaling beyond direct Python -> Postgres.
- Jooble and Kaggle are not yet integrated - `config/settings.py` already has a placeholder env var for Jooble's key, so wiring it in later is a config + one new `JobSource` class, not a redesign.
- Snowflake credentials go in `.env` (`SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_PASSWORD`, ...); `snowflake/load_to_snowflake.py` is the existing loader, currently pointed at the old Parquet-based flow and not yet updated for the new star schema.

## Setup

1. **Start Postgres.** This project has been developed against a local Postgres instance (not Docker) - if you have one running already, skip to step 2. Otherwise: `docker compose up -d` (requires Docker Desktop).
2. **Create a virtualenv and install Python dependencies:**
   ```
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Configure environment:** copy `.env.example` to `.env` and adjust if needed. For the AI assistant, set `OPENAI_API_KEY` (or point `AI_CHAT_PROVIDER`/`AI_EMBEDDING_PROVIDER` at Claude/Azure/Ollama instead) - everything else about the AI module works with no other account (see `.env.example`). For auth, set a fixed `JWT_SECRET_KEY` (a random one is generated per-process otherwise, which invalidates tokens on every restart); Google/GitHub OAuth, Redis caching, and SMTP email are all optional and degrade gracefully when unset (see the SaaS platform layer section above).
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

Registered sources live in `collector/sources/registry.py` - `remoteok` and `arbeitnow` run with no setup; `adzuna` and `usajobs` activate once you add their credentials to `.env` (see `.env.example`).

## Running the AI assistant

After running the pipeline (so there's data to index):

```
python main.py ai-index    # embeds every job posting into the RAG vector store
```

Re-run it whenever you've collected new postings and want the assistant grounded in the latest data. Then use the "Assistant" tab in the UI, or call the API directly:

```
curl -X POST http://localhost:8000/api/ai/chat -H "Content-Type: application/json" -d '{"message": "What skills are trending?"}'
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

## Running job alerts

Alert matching (`jobs/alert_matcher.py`) doesn't need Redis or Celery to run - it's a plain function:

```
python main.py check-alerts
```

Matches each active alert against current postings, logs (or sends, if `SMTP_*` is set) a notification for new matches, and advances each alert's high-water mark so re-running never double-notifies. For production, `jobs/celery_app.py` runs the same function on an hourly Celery Beat schedule once `REDIS_URL` is set:

```
celery -A jobs.celery_app worker --beat --loglevel=info
```

## Tests

```
pytest
```

Unit tests (`test_helper.py`, `test_validate.py`, `test_transform.py`, `test_geo.py`, `test_skill_categories.py`, `test_collector_registry.py`, `test_memory_vector_store.py`, `test_rate_limiter.py`, `test_rag_prompts.py`, `test_rag_chatbot_service.py`, `test_ai_router.py`, `test_auth_security.py`, `test_cache.py`) run with no dependencies and no real API calls - the AI tests inject fake `ChatProvider`/`EmbeddingProvider`/`VectorStore` implementations rather than hitting OpenAI, and `test_auth_security.py`/`test_cache.py` exercise pure functions (hashing, JWT encode/decode, the in-memory cache) directly. Integration tests (`test_connection.py`, `test_repository.py`, `test_api.py`, `test_auth_router.py`, `test_users_router.py`, `test_admin_router.py`, `test_alert_matcher.py`) need a reachable Postgres instance and skip automatically if one isn't available. All of them run against an isolated `{DB_NAME}_test` database (auto-provisioned via the `use_test_db` fixture in `tests/conftest.py`), never your real data.

## Project layout

```
collector/           sources/ (remoteok, arbeitnow, adzuna, usajobs, registry.py), retry logic, raw snapshot writer
config/               settings.py (env-backed) and constants.py
database/             schema.sql (star schema), schema_app.sql (users/auth tables), connection.py,
                      repository.py + queries.py (jobs read/write), users_repository.py + users_queries.py (accounts read/write)
etl/                  extract.py, validate.py, transform.py, load.py, pipeline.py
api/                  main.py (mounts everything under /api/v1), schemas.py, schemas_users.py
                      routes/ (jobs.py, stats.py, users.py, admin.py)
auth/                 security.py (hashing/JWT), dependencies.py (RBAC), schemas.py, router.py
                      oauth/ (google.py, github.py, base.py, state_store.py)
ai/                   providers/ (openai, claude, azure_openai, ollama, registry.py)
                      vectorstore/ (memory, pinecone, registry.py)
                      prompts/, services/ (rag_indexer, rag_chatbot_service, conversation_store, rate_limiter)
                      models/ (schemas.py), router.py
jobs/                 alert_matcher.py (matching logic), celery_app.py, tasks.py
frontend/             React + Vite + TypeScript UI (src/pages, src/components, src/api, src/context, src/hooks)
utils/                logger.py, helper.py, exceptions.py, geo.py (country inference), skill_categories.py,
                      cache.py (in-memory/Redis), rate_limiter.py, email.py, resume_storage.py
tests/                unit + integration tests
data/raw/<source>/    raw JSON snapshots per source (gitignored)
data/processed/       reserved for the future Spark stage
data/ai/              persisted RAG vector store when using the in-memory backend (gitignored)
data/resumes/         uploaded resumes, per-user UUID-named (gitignored)
logs/                 application log file (gitignored)
```
