-- Curated warehouse schema for job-market-intelligence.
-- Run once to set up the warehouse/database/schema and all tables.

CREATE WAREHOUSE IF NOT EXISTS JMI_WH WITH WAREHOUSE_SIZE = 'XSMALL' AUTO_SUSPEND = 60 AUTO_RESUME = TRUE;
CREATE DATABASE IF NOT EXISTS JMI_DB;
CREATE SCHEMA IF NOT EXISTS JMI_DB.CURATED;

USE WAREHOUSE JMI_WH;
USE DATABASE JMI_DB;
USE SCHEMA CURATED;

-- ---------------------------------------------------------------------
-- Staging: flat landing zone for whatever Spark produced. One row per
-- job posting, not yet modeled. Loaded fresh from Parquet on every run.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS STG_JOBS (
    job_id          VARCHAR,
    company         VARCHAR,
    position        VARCHAR,
    location        VARCHAR,
    salary_min      NUMBER,
    salary_max      NUMBER,
    date_posted     DATE,
    ingestion_date  DATE,
    tags            ARRAY,
    url             VARCHAR,
    apply_url       VARCHAR,
    description     VARCHAR,
    loaded_at       TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- ---------------------------------------------------------------------
-- Dimensions
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS DIM_COMPANY (
    company_key  NUMBER AUTOINCREMENT PRIMARY KEY,
    company_name VARCHAR UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS DIM_LOCATION (
    location_key  NUMBER AUTOINCREMENT PRIMARY KEY,
    location_name VARCHAR UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS DIM_TAG (
    tag_key  NUMBER AUTOINCREMENT PRIMARY KEY,
    tag_name VARCHAR UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS DIM_DATE (
    date_key     NUMBER PRIMARY KEY,          -- YYYYMMDD
    full_date    DATE UNIQUE NOT NULL,
    year         NUMBER,
    month        NUMBER,
    day          NUMBER,
    week_of_year NUMBER,
    day_of_week  VARCHAR
);

-- ---------------------------------------------------------------------
-- Fact + bridge (tags are many-to-many per job posting)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS FACT_JOB_POSTINGS (
    job_posting_key NUMBER AUTOINCREMENT PRIMARY KEY,
    job_id          VARCHAR UNIQUE NOT NULL,
    company_key     NUMBER REFERENCES DIM_COMPANY(company_key),
    location_key    NUMBER REFERENCES DIM_LOCATION(location_key),
    date_key        NUMBER REFERENCES DIM_DATE(date_key),
    position        VARCHAR,
    salary_min      NUMBER,
    salary_max      NUMBER,
    url             VARCHAR,
    apply_url       VARCHAR,
    description     VARCHAR,
    loaded_at       TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS BRIDGE_JOB_TAGS (
    job_id  VARCHAR NOT NULL,
    tag_key NUMBER REFERENCES DIM_TAG(tag_key),
    PRIMARY KEY (job_id, tag_key)
);
