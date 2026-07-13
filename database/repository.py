"""Star-schema write path (used by the ETL load step). See queries.py for
the read path used by the API."""
import json
from datetime import date as date_type

from psycopg2.extras import execute_values

from database.connection import get_db_cursor
from utils.logger import logger

_DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
_MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

_GET_OR_CREATE_SQL = """
    INSERT INTO {table} ({name_col})
    VALUES (%s)
    ON CONFLICT ({name_col}) DO UPDATE SET {name_col} = EXCLUDED.{name_col}
    RETURNING {key_col}
"""

_UPSERT_FACT_SQL = """
    INSERT INTO fact_jobs (
        source_key, external_id, company_key, location_key, date_key,
        position, remote_type, salary_min, salary_max, job_url, apply_url, description
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (source_key, external_id) DO UPDATE SET
        company_key  = EXCLUDED.company_key,
        location_key = EXCLUDED.location_key,
        date_key     = EXCLUDED.date_key,
        position     = EXCLUDED.position,
        remote_type  = EXCLUDED.remote_type,
        salary_min   = EXCLUDED.salary_min,
        salary_max   = EXCLUDED.salary_max,
        job_url      = EXCLUDED.job_url,
        apply_url    = EXCLUDED.apply_url,
        description  = EXCLUDED.description,
        updated_at   = CURRENT_TIMESTAMP
    RETURNING job_key
"""


def _get_or_create(cursor, table: str, name_col: str, key_col: str, value: str) -> int:
    cursor.execute(_GET_OR_CREATE_SQL.format(table=table, name_col=name_col, key_col=key_col), (value,))
    return cursor.fetchone()[0]


def _get_or_create_location(cursor, location_name: str, country: str | None) -> int:
    """Like _get_or_create, but also carries the (best-effort) inferred
    country. A non-null country from this run always overwrites a stale
    value; a null one never clobbers a country a previous run inferred."""
    cursor.execute(
        """
        INSERT INTO dim_location (location_name, country)
        VALUES (%s, %s)
        ON CONFLICT (location_name) DO UPDATE SET
            country = COALESCE(EXCLUDED.country, dim_location.country)
        RETURNING location_key
        """,
        (location_name, country),
    )
    return cursor.fetchone()[0]


def _get_or_create_date(cursor, day: date_type | None) -> int | None:
    if day is None:
        return None
    date_key = int(day.strftime("%Y%m%d"))
    cursor.execute(
        """
        INSERT INTO dim_date (date_key, full_date, year, month, day, week_of_year, day_of_week, month_name)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (date_key) DO NOTHING
        """,
        (
            date_key, day, day.year, day.month, day.day,
            day.isocalendar()[1], _DAY_NAMES[day.weekday()], _MONTH_NAMES[day.month - 1],
        ),
    )
    return date_key


def upsert_jobs(source: str, jobs: list[dict], dbname: str | None = None) -> int:
    """Upserts one source's normalized jobs into the star schema: resolves
    (get-or-creates) each dimension row, upserts the fact row keyed on
    (source_key, external_id), and replaces its skill-bridge rows.

    Row-at-a-time rather than bulk, trading some throughput for simple,
    obviously-correct get-or-create semantics - fine at this data volume
    (low hundreds of records per source per run)."""
    if not jobs:
        return 0

    with get_db_cursor(commit=True, dbname=dbname) as cursor:
        source_key = _get_or_create(cursor, "dim_source", "source_name", "source_key", source)

        count = 0
        for job in jobs:
            company_key = (
                _get_or_create(cursor, "dim_company", "company_name", "company_key", job["company"])
                if job.get("company") else None
            )
            location_key = (
                _get_or_create_location(cursor, job["location"], job.get("country"))
                if job.get("location") else None
            )
            date_key = _get_or_create_date(cursor, job.get("date_posted"))

            cursor.execute(
                _UPSERT_FACT_SQL,
                (
                    source_key, job["external_id"], company_key, location_key, date_key,
                    job.get("position"), job.get("remote_type"), job.get("salary_min"), job.get("salary_max"),
                    job.get("job_url"), job.get("apply_url"), job.get("description"),
                ),
            )
            job_key = cursor.fetchone()[0]

            cursor.execute("DELETE FROM bridge_job_skill WHERE job_key = %s", (job_key,))
            tags = [t for t in job.get("tags", []) if t]
            if tags:
                skill_keys = {
                    _get_or_create(cursor, "dim_skill", "skill_name", "skill_key", tag) for tag in tags
                }
                execute_values(
                    cursor,
                    "INSERT INTO bridge_job_skill (job_key, skill_key) VALUES %s ON CONFLICT DO NOTHING",
                    [(job_key, skill_key) for skill_key in skill_keys],
                )

            count += 1

    logger.info("[%s] Upserted %d job records into the star schema.", source, count)
    return count


def insert_rejected(source: str, rejected: list[tuple[dict, list[str]]], dbname: str | None = None) -> int:
    if not rejected:
        return 0

    rows = [
        (source, str(raw.get("id") or raw.get("slug") or "") or None, reasons, json.dumps(raw))
        for raw, reasons in rejected
    ]

    with get_db_cursor(commit=True, dbname=dbname) as cursor:
        execute_values(
            cursor,
            "INSERT INTO rejected_records (source_name, external_id, reasons, raw_payload) VALUES %s",
            rows,
            template="(%s, %s, %s, %s::jsonb)",
        )

    logger.info("[%s] Logged %d rejected record(s).", source, len(rows))
    return len(rows)


def count_jobs(dbname: str | None = None) -> int:
    with get_db_cursor(dbname=dbname) as cursor:
        cursor.execute("SELECT COUNT(*) FROM fact_jobs")
        return cursor.fetchone()[0]
