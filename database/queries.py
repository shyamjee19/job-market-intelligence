"""Read-only queries backing the API. Kept separate from repository.py,
which owns the ETL write path (upsert_jobs)."""
from psycopg2.extras import RealDictCursor

from database.connection import get_db_cursor
from utils.skill_categories import CATEGORY_MATCHERS

MAX_PAGE_SIZE = 100

TAGS_SUBQUERY = """
    COALESCE(
        (SELECT array_agg(sk.skill_name ORDER BY sk.skill_name)
         FROM bridge_job_skill bjs JOIN dim_skill sk ON sk.skill_key = bjs.skill_key
         WHERE bjs.job_key = f.job_key),
        '{}'
    ) AS tags
"""

JOB_SELECT = f"""
    SELECT
        f.job_key AS id,
        ds.source_name AS source,
        f.external_id,
        dc.company_name AS company,
        f.position,
        dl.location_name AS location,
        f.remote_type,
        f.salary_min,
        f.salary_max,
        dd.full_date AS date_posted,
        f.job_url,
        f.apply_url,
        {TAGS_SUBQUERY}
    FROM fact_jobs f
    LEFT JOIN dim_company dc ON dc.company_key = f.company_key
    LEFT JOIN dim_location dl ON dl.location_key = f.location_key
    LEFT JOIN dim_date dd ON dd.date_key = f.date_key
    LEFT JOIN dim_source ds ON ds.source_key = f.source_key
"""


def list_jobs(
    search: str | None = None,
    company: str | None = None,
    location: str | None = None,
    tag: str | None = None,
    source: str | None = None,
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
        where.append("(f.position ILIKE %s OR dc.company_name ILIKE %s OR f.description ILIKE %s)")
        needle = f"%{search}%"
        params.extend([needle, needle, needle])
    if company:
        where.append("dc.company_name ILIKE %s")
        params.append(f"%{company}%")
    if location:
        where.append("dl.location_name ILIKE %s")
        params.append(f"%{location}%")
    if source:
        where.append("ds.source_name = %s")
        params.append(source)
    if salary_min:
        where.append("f.salary_min >= %s")
        params.append(salary_min)
    if tag:
        where.append(
            "EXISTS (SELECT 1 FROM bridge_job_skill bjs JOIN dim_skill sk ON sk.skill_key = bjs.skill_key "
            "WHERE bjs.job_key = f.job_key AND sk.skill_name = %s)"
        )
        params.append(tag)

    where_clause = f"WHERE {' AND '.join(where)}" if where else ""

    with get_db_cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            f"""
            SELECT COUNT(*) AS total
            FROM fact_jobs f
            LEFT JOIN dim_company dc ON dc.company_key = f.company_key
            LEFT JOIN dim_location dl ON dl.location_key = f.location_key
            LEFT JOIN dim_source ds ON ds.source_key = f.source_key
            {where_clause}
            """,
            params,
        )
        total = cursor.fetchone()["total"]

        cursor.execute(
            f"""
            {JOB_SELECT}
            {where_clause}
            ORDER BY dd.full_date DESC NULLS LAST, f.job_key DESC
            LIMIT %s OFFSET %s
            """,
            [*params, page_size, (page - 1) * page_size],
        )
        rows = cursor.fetchall()

    return rows, total


def get_job_by_id(job_id: int) -> dict | None:
    with get_db_cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            f"""
            SELECT
                f.job_key AS id,
                ds.source_name AS source,
                f.external_id,
                dc.company_name AS company,
                f.position,
                dl.location_name AS location,
                f.remote_type,
                f.salary_min,
                f.salary_max,
                dd.full_date AS date_posted,
                f.job_url,
                f.apply_url,
                f.description,
                f.created_at,
                f.updated_at,
                {TAGS_SUBQUERY}
            FROM fact_jobs f
            LEFT JOIN dim_company dc ON dc.company_key = f.company_key
            LEFT JOIN dim_location dl ON dl.location_key = f.location_key
            LEFT JOIN dim_date dd ON dd.date_key = f.date_key
            LEFT JOIN dim_source ds ON ds.source_key = f.source_key
            WHERE f.job_key = %s
            """,
            (job_id,),
        )
        return cursor.fetchone()


def summary_stats() -> dict:
    with get_db_cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_jobs,
                COUNT(*) FILTER (WHERE dd.full_date = CURRENT_DATE) AS today_jobs,
                COUNT(*) FILTER (WHERE f.remote_type = 'remote') AS remote_jobs,
                COUNT(*) FILTER (WHERE f.remote_type = 'hybrid') AS hybrid_jobs,
                COUNT(*) FILTER (WHERE f.remote_type = 'onsite') AS onsite_jobs,
                COUNT(DISTINCT f.company_key) AS total_companies,
                COUNT(DISTINCT f.location_key) AS total_locations,
                ROUND(AVG(f.salary_min)) AS avg_salary_min,
                ROUND(AVG(f.salary_max)) AS avg_salary_max,
                MAX(f.salary_max) AS highest_salary
            FROM fact_jobs f
            LEFT JOIN dim_date dd ON dd.date_key = f.date_key
            """
        )
        return cursor.fetchone()


def top_companies(limit: int = 10, source: str | None = None) -> list[dict]:
    where = "WHERE ds.source_name = %s" if source else ""
    params = [source] if source else []
    with get_db_cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            f"""
            SELECT dc.company_name AS company, COUNT(*) AS count
            FROM fact_jobs f
            JOIN dim_company dc ON dc.company_key = f.company_key
            LEFT JOIN dim_source ds ON ds.source_key = f.source_key
            {where}
            GROUP BY dc.company_name
            ORDER BY count DESC
            LIMIT %s
            """,
            [*params, limit],
        )
        return cursor.fetchall()


def top_tags(limit: int = 15, source: str | None = None, category: str | None = None) -> list[dict]:
    """`category` (one of utils.skill_categories.CATEGORY_MATCHERS, e.g.
    "ai"/"cloud"/"tech") filters by keyword match in Python after
    fetching every tag's count - the skill dimension is small (low
    hundreds of rows), so this is simpler than replicating the keyword
    lists as SQL and just as fast at this scale."""
    where = "WHERE ds.source_name = %s" if source else ""
    params = [source] if source else []
    with get_db_cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            f"""
            SELECT sk.skill_name AS tag, COUNT(*) AS count
            FROM bridge_job_skill bjs
            JOIN dim_skill sk ON sk.skill_key = bjs.skill_key
            JOIN fact_jobs f ON f.job_key = bjs.job_key
            LEFT JOIN dim_source ds ON ds.source_key = f.source_key
            {where}
            GROUP BY sk.skill_name
            ORDER BY count DESC
            """,
            params,
        )
        rows = cursor.fetchall()

    if category:
        matcher = CATEGORY_MATCHERS.get(category)
        if matcher:
            rows = [row for row in rows if matcher(row["tag"])]

    return rows[:limit]


def postings_by_date() -> list[dict]:
    with get_db_cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT dd.full_date AS date_posted, COUNT(*) AS count
            FROM fact_jobs f
            JOIN dim_date dd ON dd.date_key = f.date_key
            GROUP BY dd.full_date
            ORDER BY dd.full_date
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
            FROM fact_jobs
            WHERE salary_min IS NOT NULL
            GROUP BY bucket_start
            ORDER BY bucket_start
            """
        )
        return cursor.fetchall()


def sources_breakdown() -> list[dict]:
    with get_db_cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT ds.source_name AS source, COUNT(*) AS count
            FROM fact_jobs f
            JOIN dim_source ds ON ds.source_key = f.source_key
            GROUP BY ds.source_name
            ORDER BY count DESC
            """
        )
        return cursor.fetchall()


def hiring_map() -> list[dict]:
    """Postings per country, for the world map. Country is a best-effort
    inference from free-text location (see utils/geo.py) - postings whose
    location didn't match a known country/city are excluded here rather
    than counted as "unknown", since the map has nowhere to put them."""
    with get_db_cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT dl.country, COUNT(*) AS count
            FROM fact_jobs f
            JOIN dim_location dl ON dl.location_key = f.location_key
            WHERE dl.country IS NOT NULL
            GROUP BY dl.country
            ORDER BY count DESC
            """
        )
        return cursor.fetchall()


def hiring_trend() -> dict:
    """Today's postings vs yesterday's, for the dashboard's trend tile."""
    with get_db_cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT
                COUNT(*) FILTER (WHERE dd.full_date = CURRENT_DATE) AS today_count,
                COUNT(*) FILTER (WHERE dd.full_date = CURRENT_DATE - 1) AS yesterday_count
            FROM fact_jobs f
            JOIN dim_date dd ON dd.date_key = f.date_key
            """
        )
        row = cursor.fetchone()

    today, yesterday = row["today_count"], row["yesterday_count"]
    pct_change = round((today - yesterday) / yesterday * 100) if yesterday else None
    return {"today_count": today, "yesterday_count": yesterday, "pct_change": pct_change}


def list_companies(limit: int = 50) -> list[dict]:
    return top_companies(limit=limit)


def list_skills(limit: int = 50) -> list[dict]:
    return top_tags(limit=limit)


def list_all_jobs_for_indexing() -> list[dict]:
    """Every job's full detail (including description), for the AI
    module's RAG indexer - not paginated, since it's meant to run as a
    batch job over the whole table, not serve a page request."""
    with get_db_cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            f"""
            SELECT
                f.job_key AS id,
                ds.source_name AS source,
                dc.company_name AS company,
                f.position,
                dl.location_name AS location,
                f.remote_type,
                f.salary_min,
                f.salary_max,
                f.description,
                {TAGS_SUBQUERY}
            FROM fact_jobs f
            LEFT JOIN dim_company dc ON dc.company_key = f.company_key
            LEFT JOIN dim_location dl ON dl.location_key = f.location_key
            LEFT JOIN dim_source ds ON ds.source_key = f.source_key
            ORDER BY f.job_key
            """
        )
        return cursor.fetchall()
