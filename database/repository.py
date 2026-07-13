from psycopg2.extras import execute_values

from database.connection import get_db_cursor
from utils.logger import logger

_UPSERT_SQL = """
    INSERT INTO jobs (
        job_id, company, position, location, salary_min, salary_max,
        date_posted, tags, job_url, apply_url, description
    )
    VALUES %s
    ON CONFLICT (job_id) DO UPDATE SET
        company     = EXCLUDED.company,
        position    = EXCLUDED.position,
        location    = EXCLUDED.location,
        salary_min  = EXCLUDED.salary_min,
        salary_max  = EXCLUDED.salary_max,
        date_posted = EXCLUDED.date_posted,
        tags        = EXCLUDED.tags,
        job_url     = EXCLUDED.job_url,
        apply_url   = EXCLUDED.apply_url,
        description = EXCLUDED.description,
        updated_at  = CURRENT_TIMESTAMP
"""


def upsert_jobs(jobs: list[dict], dbname: str | None = None) -> int:
    """Bulk insert-or-update jobs keyed on job_id. Returns the number of
    records submitted (not distinguishing inserts from updates)."""
    if not jobs:
        return 0

    rows = [
        (
            job["job_id"],
            job.get("company"),
            job.get("position"),
            job.get("location"),
            job.get("salary_min"),
            job.get("salary_max"),
            job.get("date_posted"),
            job.get("tags", []),
            job.get("job_url"),
            job.get("apply_url"),
            job.get("description"),
        )
        for job in jobs
    ]

    with get_db_cursor(commit=True, dbname=dbname) as cursor:
        execute_values(cursor, _UPSERT_SQL, rows)

    logger.info("Upserted %d job records into the database.", len(rows))
    return len(rows)


def count_jobs(dbname: str | None = None) -> int:
    with get_db_cursor(dbname=dbname) as cursor:
        cursor.execute("SELECT COUNT(*) FROM jobs")
        return cursor.fetchone()[0]
