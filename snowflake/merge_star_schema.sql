
-- Populates the star schema from whatever currently sits in STG_JOBS.
-- Idempotent: safe to run after every load, only inserts what's missing
-- and updates facts that already exist (matched on job_id).

USE WAREHOUSE JMI_WH;
USE DATABASE JMI_DB;
USE SCHEMA CURATED;

-- 1. Dimensions -----------------------------------------------------------

MERGE INTO DIM_COMPANY d
USING (SELECT DISTINCT company AS company_name FROM STG_JOBS WHERE company IS NOT NULL) s
ON d.company_name = s.company_name
WHEN NOT MATCHED THEN INSERT (company_name) VALUES (s.company_name);

MERGE INTO DIM_LOCATION d
USING (SELECT DISTINCT location AS location_name FROM STG_JOBS WHERE location IS NOT NULL) s
ON d.location_name = s.location_name
WHEN NOT MATCHED THEN INSERT (location_name) VALUES (s.location_name);

MERGE INTO DIM_TAG d
USING (
    SELECT DISTINCT f.value::string AS tag_name
    FROM STG_JOBS, LATERAL FLATTEN(input => tags) f
) s
ON d.tag_name = s.tag_name
WHEN NOT MATCHED THEN INSERT (tag_name) VALUES (s.tag_name);

MERGE INTO DIM_DATE d
USING (
    SELECT DISTINCT
        date_posted AS full_date,
        TO_NUMBER(TO_CHAR(date_posted, 'YYYYMMDD')) AS date_key,
        YEAR(date_posted) AS year,
        MONTH(date_posted) AS month,
        DAY(date_posted) AS day,
        WEEKOFYEAR(date_posted) AS week_of_year,
        DAYNAME(date_posted) AS day_of_week
    FROM STG_JOBS
    WHERE date_posted IS NOT NULL
) s
ON d.date_key = s.date_key
WHEN NOT MATCHED THEN INSERT (date_key, full_date, year, month, day, week_of_year, day_of_week)
    VALUES (s.date_key, s.full_date, s.year, s.month, s.day, s.week_of_year, s.day_of_week);

-- 2. Fact -------------------------------------------------------------------

MERGE INTO FACT_JOB_POSTINGS f
USING (
    SELECT
        stg.job_id,
        dc.company_key,
        dl.location_key,
        TO_NUMBER(TO_CHAR(stg.date_posted, 'YYYYMMDD')) AS date_key,
        stg.position,
        stg.salary_min,
        stg.salary_max,
        stg.url,
        stg.apply_url,
        stg.description
    FROM STG_JOBS stg
    LEFT JOIN DIM_COMPANY dc ON dc.company_name = stg.company
    LEFT JOIN DIM_LOCATION dl ON dl.location_name = stg.location
) s
ON f.job_id = s.job_id
WHEN MATCHED THEN UPDATE SET
    company_key  = s.company_key,
    location_key = s.location_key,
    date_key     = s.date_key,
    position     = s.position,
    salary_min   = s.salary_min,
    salary_max   = s.salary_max,
    url          = s.url,
    apply_url    = s.apply_url,
    description  = s.description
WHEN NOT MATCHED THEN INSERT
    (job_id, company_key, location_key, date_key, position, salary_min, salary_max, url, apply_url, description)
    VALUES
    (s.job_id, s.company_key, s.location_key, s.date_key, s.position, s.salary_min, s.salary_max, s.url, s.apply_url, s.description);

-- 3. Bridge (job <-> tag) -----------------------------------------------------

MERGE INTO BRIDGE_JOB_TAGS b
USING (
    SELECT DISTINCT stg.job_id, dt.tag_key
    FROM STG_JOBS stg, LATERAL FLATTEN(input => stg.tags) f
    JOIN DIM_TAG dt ON dt.tag_name = f.value::string
) s
ON b.job_id = s.job_id AND b.tag_key = s.tag_key
WHEN NOT MATCHED THEN INSERT (job_id, tag_key) VALUES (s.job_id, s.tag_key);
