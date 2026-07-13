-- job_id is the natural key from the source API: unique so re-running the
-- pipeline upserts existing postings instead of duplicating them.
CREATE TABLE IF NOT EXISTS jobs (
    id              SERIAL PRIMARY KEY,
    job_id          BIGINT UNIQUE NOT NULL,
    company         VARCHAR(255),
    position        VARCHAR(255),
    location        VARCHAR(255),
    salary_min      INTEGER,
    salary_max      INTEGER,
    date_posted     DATE,
    tags            TEXT[] NOT NULL DEFAULT '{}',
    job_url         TEXT,
    apply_url       TEXT,
    description     TEXT,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs (company);
CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs (location);
CREATE INDEX IF NOT EXISTS idx_jobs_date_posted ON jobs (date_posted);
CREATE INDEX IF NOT EXISTS idx_jobs_tags ON jobs USING GIN (tags);
