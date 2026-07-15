"""Read path for users, profiles, saved jobs, favorites, alerts, audit
logs, and admin views. See users_repository.py for the write path."""
from psycopg2.extras import RealDictCursor

from database.connection import get_db_cursor
from database.queries import JOB_SELECT, MAX_PAGE_SIZE

_USER_COLUMNS = "user_id, email, hashed_password, full_name, role, google_id, github_id, is_active, created_at"


def get_user_by_id(user_id: int) -> dict | None:
    with get_db_cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(f"SELECT {_USER_COLUMNS} FROM users WHERE user_id = %s", (user_id,))
        return cursor.fetchone()


def get_user_by_email(email: str) -> dict | None:
    with get_db_cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(f"SELECT {_USER_COLUMNS} FROM users WHERE email = %s", (email,))
        return cursor.fetchone()


def get_user_by_oauth_id(provider: str, provider_id: str) -> dict | None:
    column = "google_id" if provider == "google" else "github_id"
    with get_db_cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(f"SELECT {_USER_COLUMNS} FROM users WHERE {column} = %s", (provider_id,))
        return cursor.fetchone()


def get_valid_refresh_token(token_hash: str) -> dict | None:
    with get_db_cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT * FROM refresh_tokens
            WHERE token_hash = %s AND revoked = FALSE AND expires_at > CURRENT_TIMESTAMP
            """,
            (token_hash,),
        )
        return cursor.fetchone()


def get_valid_password_reset_token(token_hash: str) -> dict | None:
    with get_db_cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT * FROM password_reset_tokens
            WHERE token_hash = %s AND used = FALSE AND expires_at > CURRENT_TIMESTAMP
            """,
            (token_hash,),
        )
        return cursor.fetchone()


def list_notifications(user_id: int, page: int = 1, page_size: int = 20) -> tuple[list[dict], int]:
    page_size = min(max(page_size, 1), MAX_PAGE_SIZE)
    page = max(page, 1)

    with get_db_cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("SELECT COUNT(*) AS total FROM notification_log WHERE user_id = %s", (user_id,))
        total = cursor.fetchone()["total"]

        cursor.execute(
            """
            SELECT * FROM notification_log WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """,
            (user_id, page_size, (page - 1) * page_size),
        )
        rows = cursor.fetchall()

    return rows, total


def count_unread_notifications(user_id: int) -> int:
    with get_db_cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("SELECT COUNT(*) AS n FROM notification_log WHERE user_id = %s AND NOT is_read", (user_id,))
        return cursor.fetchone()["n"]


def get_profile(user_id: int) -> dict | None:
    with get_db_cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("SELECT * FROM user_profiles WHERE user_id = %s", (user_id,))
        return cursor.fetchone()


def list_saved_jobs(user_id: int) -> list[dict]:
    with get_db_cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            f"""
            {JOB_SELECT}
            JOIN saved_jobs sj ON sj.job_key = f.job_key
            WHERE sj.user_id = %s
            ORDER BY sj.saved_at DESC
            """,
            (user_id,),
        )
        return cursor.fetchall()


def get_company_key_by_name(company_name: str) -> int | None:
    with get_db_cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("SELECT company_key FROM dim_company WHERE company_name = %s", (company_name,))
        row = cursor.fetchone()
        return row["company_key"] if row else None


def list_favorite_companies(user_id: int) -> list[dict]:
    with get_db_cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT dc.company_key, dc.company_name, fc.favorited_at
            FROM favorite_companies fc
            JOIN dim_company dc ON dc.company_key = fc.company_key
            WHERE fc.user_id = %s
            ORDER BY fc.favorited_at DESC
            """,
            (user_id,),
        )
        return cursor.fetchall()


def list_alerts(user_id: int) -> list[dict]:
    with get_db_cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("SELECT * FROM job_alerts WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
        return cursor.fetchall()


def get_alert(alert_id: int, user_id: int) -> dict | None:
    with get_db_cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("SELECT * FROM job_alerts WHERE alert_id = %s AND user_id = %s", (alert_id, user_id))
        return cursor.fetchone()


def list_active_alerts() -> list[dict]:
    """Every active alert, for the background matcher (jobs/tasks.py) to
    sweep - frequency/backoff logic lives there, not in this query."""
    with get_db_cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("SELECT * FROM job_alerts WHERE is_active = TRUE")
        return cursor.fetchall()


def match_jobs_for_alert(alert: dict, limit: int = 20) -> list[dict]:
    """Postings matching an alert's saved criteria, newer than the last
    one it already notified about (job_key is assigned in insertion
    order, so "greater than" means "arrived since")."""
    where = ["1=1"]
    params: list = []

    if alert.get("last_notified_job_key"):
        where.append("f.job_key > %s")
        params.append(alert["last_notified_job_key"])
    if alert.get("keywords"):
        where.append("(f.position ILIKE %s OR f.description ILIKE %s)")
        needle = f"%{alert['keywords']}%"
        params.extend([needle, needle])
    if alert.get("location"):
        where.append("dl.location_name ILIKE %s")
        params.append(f"%{alert['location']}%")
    if alert.get("source"):
        where.append("ds.source_name = %s")
        params.append(alert["source"])
    if alert.get("salary_min"):
        where.append("f.salary_min >= %s")
        params.append(alert["salary_min"])
    if alert.get("remote_type"):
        where.append("f.remote_type = %s")
        params.append(alert["remote_type"])
    if alert.get("tag"):
        where.append(
            "EXISTS (SELECT 1 FROM bridge_job_skill bjs JOIN dim_skill sk ON sk.skill_key = bjs.skill_key "
            "WHERE bjs.job_key = f.job_key AND sk.skill_name = %s)"
        )
        params.append(alert["tag"])

    with get_db_cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            f"""
            {JOB_SELECT}
            WHERE {" AND ".join(where)}
            ORDER BY f.job_key DESC
            LIMIT %s
            """,
            [*params, limit],
        )
        return cursor.fetchall()


def list_users(page: int = 1, page_size: int = 50) -> tuple[list[dict], int]:
    page_size = min(max(page_size, 1), MAX_PAGE_SIZE)
    page = max(page, 1)

    with get_db_cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute("SELECT COUNT(*) AS total FROM users")
        total = cursor.fetchone()["total"]

        cursor.execute(
            f"""
            SELECT {_USER_COLUMNS.replace("hashed_password, ", "")}
            FROM users
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """,
            (page_size, (page - 1) * page_size),
        )
        rows = cursor.fetchall()

    return rows, total


def list_audit_logs(page: int = 1, page_size: int = 50, user_id: int | None = None) -> tuple[list[dict], int]:
    page_size = min(max(page_size, 1), MAX_PAGE_SIZE)
    page = max(page, 1)

    where = "WHERE user_id = %s" if user_id else ""
    params = [user_id] if user_id else []

    with get_db_cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(f"SELECT COUNT(*) AS total FROM audit_logs {where}", params)
        total = cursor.fetchone()["total"]

        cursor.execute(
            f"""
            SELECT * FROM audit_logs {where}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """,
            [*params, page_size, (page - 1) * page_size],
        )
        rows = cursor.fetchall()

    return rows, total


def admin_stats() -> dict:
    with get_db_cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_users,
                COUNT(*) FILTER (WHERE role = 'admin') AS admin_users,
                COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE) AS new_users_today,
                COUNT(*) FILTER (WHERE is_active) AS active_users
            FROM users
            """
        )
        return cursor.fetchone()
