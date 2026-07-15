-- Application/OLTP schema: users, auth, saved jobs, favorites, alerts,
-- audit log. Kept separate from schema.sql (the analytics star schema)
-- since these are transactional tables with a different access pattern
-- and lifecycle than the job-data warehouse - but they reference it
-- (fact_jobs, dim_company), so this file must run after schema.sql.

CREATE TABLE IF NOT EXISTS users (
    user_id          SERIAL PRIMARY KEY,
    email            VARCHAR(255) UNIQUE NOT NULL,
    hashed_password  VARCHAR(255),              -- NULL for OAuth-only accounts
    full_name        VARCHAR(255),
    role             VARCHAR(16) NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    google_id        VARCHAR(255) UNIQUE,
    github_id        VARCHAR(255) UNIQUE,
    is_active        BOOLEAN NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT users_has_login_method CHECK (
        hashed_password IS NOT NULL OR google_id IS NOT NULL OR github_id IS NOT NULL
    )
);

CREATE TABLE IF NOT EXISTS user_profiles (
    user_id             INTEGER PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    headline            VARCHAR(255),
    bio                 TEXT,
    location            VARCHAR(255),
    skills              TEXT[] NOT NULL DEFAULT '{}',
    experience_years    INTEGER,
    resume_filename     VARCHAR(255),
    resume_path         TEXT,
    resume_uploaded_at  TIMESTAMP,
    updated_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS refresh_tokens (
    token_id    SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    token_hash  VARCHAR(255) UNIQUE NOT NULL,   -- never store the raw refresh token
    expires_at  TIMESTAMP NOT NULL,
    revoked     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS saved_jobs (
    user_id   INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    job_key   INTEGER NOT NULL REFERENCES fact_jobs(job_key) ON DELETE CASCADE,
    saved_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, job_key)
);

CREATE TABLE IF NOT EXISTS favorite_companies (
    user_id       INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    company_key   INTEGER NOT NULL REFERENCES dim_company(company_key) ON DELETE CASCADE,
    favorited_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, company_key)
);

CREATE TABLE IF NOT EXISTS job_alerts (
    alert_id               SERIAL PRIMARY KEY,
    user_id                INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    name                   VARCHAR(255) NOT NULL,
    keywords               VARCHAR(255),
    location               VARCHAR(255),
    tag                    VARCHAR(128),
    source                 VARCHAR(64),
    salary_min             INTEGER,
    remote_type            VARCHAR(16),
    frequency              VARCHAR(16) NOT NULL DEFAULT 'daily' CHECK (frequency IN ('instant', 'daily', 'weekly')),
    is_active              BOOLEAN NOT NULL DEFAULT TRUE,
    last_checked_at        TIMESTAMP,
    last_notified_job_key  INTEGER,     -- high-water mark so the same posting isn't re-notified
    created_at             TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Every notification "sent" lands here regardless of whether real email
-- delivery is configured - status stays 'logged' until utils/email.py has
-- real SMTP/API credentials, so the alert pipeline is fully testable
-- without waiting on that.
CREATE TABLE IF NOT EXISTS notification_log (
    notification_id  SERIAL PRIMARY KEY,
    user_id           INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    alert_id          INTEGER REFERENCES job_alerts(alert_id) ON DELETE SET NULL,
    subject           VARCHAR(255),
    body              TEXT,
    status            VARCHAR(16) NOT NULL DEFAULT 'logged' CHECK (status IN ('logged', 'sent', 'failed')),
    created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    log_id         SERIAL PRIMARY KEY,
    user_id        INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    action         VARCHAR(64) NOT NULL,    -- e.g. 'login', 'register', 'role_change', 'resume_upload'
    resource_type  VARCHAR(64),
    resource_id    VARCHAR(64),
    metadata       JSONB,
    ip_address     VARCHAR(64),
    created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Recorded at registration time for a real compliance trail, not just a
-- client-side checkbox that leaves no server-side evidence of consent.
ALTER TABLE users ADD COLUMN IF NOT EXISTS terms_accepted_at TIMESTAMP;

-- Same hashed-token-at-rest pattern as refresh_tokens: a leaked database
-- shouldn't hand out live password-reset capability.
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    token_id    SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    token_hash  VARCHAR(255) UNIQUE NOT NULL,
    expires_at  TIMESTAMP NOT NULL,
    used        BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE notification_log ADD COLUMN IF NOT EXISTS is_read BOOLEAN NOT NULL DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_saved_jobs_user ON saved_jobs (user_id);
CREATE INDEX IF NOT EXISTS idx_favorite_companies_user ON favorite_companies (user_id);
CREATE INDEX IF NOT EXISTS idx_job_alerts_user ON job_alerts (user_id);
CREATE INDEX IF NOT EXISTS idx_job_alerts_active ON job_alerts (is_active) WHERE is_active;
CREATE INDEX IF NOT EXISTS idx_notification_log_user ON notification_log (user_id);
CREATE INDEX IF NOT EXISTS idx_notification_log_unread ON notification_log (user_id) WHERE NOT is_read;
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs (user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs (created_at);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens (user_id);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user ON password_reset_tokens (user_id);
