"""Read-only queries backing the API. Kept separate from repository.py,
which owns the ETL write path (upsert_jobs)."""
from psycopg2.extras import RealDictCursor

from database.connection import get_db_cursor

MAX_PAGE_SIZE = 100


def list_jobs(
    search: str | None = None,
    company: str | None = None,
    location: str | None = None,
    tag: str | None = None,
    salary_min: int | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[dict], int]:
    """Returns (rows, total_matching_count)."""
    page_size = min(max(page_size, 1), MAX_PAGE_SIZE)
    page = max(page, 1)

    where = []
    params: list = []

    if search:
        where.append("(position ILIKE %s OR company ILIKE %s OR description ILIKE %s)")
        needle = f"%{search}%"
        params.extend([needle, needle, needle])
    if company:
        where.append("company ILIKE %s")
        params.append(f"%{company}%")
    if location:
        where.append("location ILIKE %s")
        params.append(f"%{location}%")
    if tag:
        where.append("%s = ANY(tags)")
        params.append(tag)
    if salary_min:
        where.append("salary_min >= %s")
        params.append(salary_min)

    where_clause = f"WHERE {' AND '.join(where)}" if where else ""

    with get_db_cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(f"SELECT COUNT(*) AS total FROM jobs {where_clause}", params)
        total = cursor.fetchone()["total"]

        cursor.execute(
            f"""
            SELECT job_id, company, position, location, salary_min, salary_max,
                   date_posted, tags, job_url, apply_url
            FROM jobs
            {where_clause}
            ORDER BY date_posted DESC NULLS LAST, job_id DESC
            LIMIT %s OFFSET %s
            """,
            [*params, page_size, (page - 1) * page_size],
        )
        rows = cursor.fetchall()

    return rows, total


def get_job_by_id(job_id: int) -> dict | None:
    with get_db_cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("SELECT * FROM jobs WHERE job_id = %s", (job_id,))
        return cursor.fetchone()


def summary_stats() -> dict:
    with get_db_cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_jobs,
                COUNT(DISTINCT company) AS total_companies,
                COUNT(DISTINCT location) AS total_locations,
                ROUND(AVG(salary_min)) AS avg_salary_min,
                ROUND(AVG(salary_max)) AS avg_salary_max
            FROM jobs
            """
        )
        return cursor.fetchone()


def top_companies(limit: int = 10) -> list[dict]:
    with get_db_cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT company, COUNT(*) AS count
            FROM jobs
            WHERE company IS NOT NULL
            GROUP BY company
            ORDER BY count DESC
            LIMIT %s
            """,
            (limit,),
        )
        return cursor.fetchall()


def top_tags(limit: int = 15) -> list[dict]:
    with get_db_cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT UNNEST(tags) AS tag, COUNT(*) AS count
            FROM jobs
            GROUP BY tag
            ORDER BY count DESC
            LIMIT %s
            """,
            (limit,),
        )
        return cursor.fetchall()


def postings_by_date() -> list[dict]:
    with get_db_cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT date_posted, COUNT(*) AS count
            FROM jobs
            WHERE date_posted IS NOT NULL
            GROUP BY date_posted
            ORDER BY date_posted
            """
        )
        return cursor.fetchall()


def salary_distribution() -> list[dict]:
    """Buckets postings with a known salary_min into $20k-wide bands."""
    with get_db_cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT
                (FLOOR(salary_min / 20000) * 20000)::INT AS bucket_start,
                COUNT(*) AS count
            FROM jobs
            WHERE salary_min IS NOT NULL
            GROUP BY bucket_start
            ORDER BY bucket_start
            """
        )
        return cursor.fetchall()
