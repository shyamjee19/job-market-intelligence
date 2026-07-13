-- Star schema for job-market-intelligence.
--
-- Fact_Jobs holds one row per job posting per source. A posting is
-- identified by (source_key, external_id) - the source's own id/slug -
-- since two different sources can reuse the same numeric id independently.
-- Dimensions are get-or-create: the loader looks up or inserts by natural
-- key and never duplicates a company/location/skill/date/source row.

CREATE TABLE IF NOT EXISTS dim_source (
    source_key   SERIAL PRIMARY KEY,
    source_name  VARCHAR(64) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_company (
    company_key   SERIAL PRIMARY KEY,
    company_name  VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_location (
    location_key   SERIAL PRIMARY KEY,
    location_name  VARCHAR(255) UNIQUE NOT NULL,
    country         VARCHAR(128),
    city            VARCHAR(128)
);

CREATE TABLE IF NOT EXISTS dim_skill (
    skill_key   SERIAL PRIMARY KEY,
    skill_name  VARCHAR(128) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_key      INTEGER PRIMARY KEY,        -- YYYYMMDD
    full_date     DATE UNIQUE NOT NULL,
    year          INTEGER NOT NULL,
    month         INTEGER NOT NULL,
    day           INTEGER NOT NULL,
    week_of_year  INTEGER NOT NULL,
    day_of_week   VARCHAR(16) NOT NULL,
    month_name    VARCHAR(16) NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_jobs (
    job_key       SERIAL PRIMARY KEY,
    source_key    INTEGER NOT NULL REFERENCES dim_source(source_key),
    external_id   VARCHAR(255) NOT NULL,        -- the source's own job id/slug
    company_key   INTEGER REFERENCES dim_company(company_key),
    location_key  INTEGER REFERENCES dim_location(location_key),
    date_key      INTEGER REFERENCES dim_date(date_key),
    position      VARCHAR(500),
    remote_type   VARCHAR(16),                  -- 'remote' | 'onsite' (best-effort; no hybrid signal yet)
    salary_min    INTEGER,
    salary_max    INTEGER,
    job_url       TEXT,
    apply_url     TEXT,
    description   TEXT,
    created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (source_key, external_id)
);

CREATE TABLE IF NOT EXISTS bridge_job_skill (
    job_key    INTEGER NOT NULL REFERENCES fact_jobs(job_key) ON DELETE CASCADE,
    skill_key  INTEGER NOT NULL REFERENCES dim_skill(skill_key),
    PRIMARY KEY (job_key, skill_key)
);

-- Rejected records are kept for data-quality visibility instead of being
-- silently dropped - see etl/validate.py.
CREATE TABLE IF NOT EXISTS rejected_records (
    id           SERIAL PRIMARY KEY,
    source_name  VARCHAR(64) NOT NULL,
    external_id  VARCHAR(255),
    reasons      TEXT[] NOT NULL,
    raw_payload  JSONB NOT NULL,
    rejected_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_fact_jobs_company ON fact_jobs (company_key);
CREATE INDEX IF NOT EXISTS idx_fact_jobs_location ON fact_jobs (location_key);
CREATE INDEX IF NOT EXISTS idx_fact_jobs_date ON fact_jobs (date_key);
CREATE INDEX IF NOT EXISTS idx_fact_jobs_source ON fact_jobs (source_key);
CREATE INDEX IF NOT EXISTS idx_bridge_job_skill_skill ON bridge_job_skill (skill_key);
