"""Write path for users, profiles, saved jobs, favorites, alerts, audit
and notification logs. See users_queries.py for the read path."""
import json
from datetime import datetime

from psycopg2.extras import RealDictCursor

from database.connection import get_db_cursor


def create_user(
    email: str,
    hashed_password: str | None = None,
    full_name: str | None = None,
    google_id: str | None = None,
    github_id: str | None = None,
) -> dict:
    with get_db_cursor(commit=True, cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            """
            INSERT INTO users (email, hashed_password, full_name, google_id, github_id)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING user_id, email, full_name, role, is_active, created_at
            """,
            (email, hashed_password, full_name, google_id, github_id),
        )
        return cursor.fetchone()


def link_oauth_id(user_id: int, provider: str, provider_id: str) -> None:
    # `column` is one of two hardcoded literals below, never interpolated
    # user input, so this f-string doesn't open a SQL-injection path.
    column = "google_id" if provider == "google" else "github_id"
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            f"UPDATE users SET {column} = %s, updated_at = CURRENT_TIMESTAMP WHERE user_id = %s",
            (provider_id, user_id),
        )


def set_user_role(user_id: int, role: str) -> None:
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("UPDATE users SET role = %s, updated_at = CURRENT_TIMESTAMP WHERE user_id = %s", (role, user_id))


def set_user_active(user_id: int, is_active: bool) -> None:
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "UPDATE users SET is_active = %s, updated_at = CURRENT_TIMESTAMP WHERE user_id = %s", (is_active, user_id)
        )


def store_refresh_token(user_id: int, token_hash: str, expires_at: datetime) -> None:
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "INSERT INTO refresh_tokens (user_id, token_hash, expires_at) VALUES (%s, %s, %s)",
            (user_id, token_hash, expires_at),
        )


def revoke_refresh_token(token_hash: str) -> None:
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("UPDATE refresh_tokens SET revoked = TRUE WHERE token_hash = %s", (token_hash,))


def revoke_all_refresh_tokens(user_id: int) -> None:
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("UPDATE refresh_tokens SET revoked = TRUE WHERE user_id = %s", (user_id,))


def upsert_profile(user_id: int, **fields) -> None:
    """`fields` may contain any of: headline, bio, location, skills,
    experience_years - only the given keys are updated. Column names are
    interpolated into the query text below, but callers only ever pass
    kwargs sourced from auth.schemas.ProfileUpdateRequest's fixed field
    list (see auth/router.py), never a raw user-controlled dict, so this
    can't become a SQL-injection path."""
    if not fields:
        return

    columns = list(fields.keys())
    placeholders = ", ".join(f"{col} = %s" for col in columns)
    values = [fields[col] for col in columns]

    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            f"""
            INSERT INTO user_profiles (user_id, {", ".join(columns)})
            VALUES (%s, {", ".join(["%s"] * len(columns))})
            ON CONFLICT (user_id) DO UPDATE SET {placeholders}, updated_at = CURRENT_TIMESTAMP
            """,
            [user_id, *values, *values],
        )


def set_resume(user_id: int, filename: str, path: str) -> None:
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO user_profiles (user_id, resume_filename, resume_path, resume_uploaded_at)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id) DO UPDATE SET
                resume_filename = EXCLUDED.resume_filename,
                resume_path = EXCLUDED.resume_path,
                resume_uploaded_at = EXCLUDED.resume_uploaded_at,
                updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, filename, path),
        )


def save_job(user_id: int, job_key: int) -> None:
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "INSERT INTO saved_jobs (user_id, job_key) VALUES (%s, %s) ON CONFLICT DO NOTHING", (user_id, job_key)
        )


def unsave_job(user_id: int, job_key: int) -> None:
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM saved_jobs WHERE user_id = %s AND job_key = %s", (user_id, job_key))


def favorite_company(user_id: int, company_key: int) -> None:
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "INSERT INTO favorite_companies (user_id, company_key) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (user_id, company_key),
        )


def unfavorite_company(user_id: int, company_key: int) -> None:
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM favorite_companies WHERE user_id = %s AND company_key = %s", (user_id, company_key))


def create_alert(user_id: int, **fields) -> dict:
    # Same reasoning as upsert_profile above: columns come from
    # api/routes/alerts.py's fixed Pydantic model fields, not raw input.
    columns = list(fields.keys())
    with get_db_cursor(commit=True, cursor_factory=RealDictCursor) as cursor:
        cursor.execute(
            f"""
            INSERT INTO job_alerts (user_id, {", ".join(columns)})
            VALUES (%s, {", ".join(["%s"] * len(columns))})
            RETURNING *
            """,
            [user_id, *[fields[c] for c in columns]],
        )
        return cursor.fetchone()


def delete_alert(alert_id: int, user_id: int) -> None:
    with get_db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM job_alerts WHERE alert_id = %s AND user_id = %s", (alert_id, user_id))


def set_alert_active(alert_id: int, user_id: int, is_active: bool) -> None:
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            "UPDATE job_alerts SET is_active = %s WHERE alert_id = %s AND user_id = %s",
            (is_active, alert_id, user_id),
        )


def mark_alert_checked(alert_id: int, last_notified_job_key: int | None = None) -> None:
    with get_db_cursor(commit=True) as cursor:
        if last_notified_job_key is not None:
            cursor.execute(
                "UPDATE job_alerts SET last_checked_at = CURRENT_TIMESTAMP, last_notified_job_key = %s WHERE alert_id = %s",
                (last_notified_job_key, alert_id),
            )
        else:
            cursor.execute(
                "UPDATE job_alerts SET last_checked_at = CURRENT_TIMESTAMP WHERE alert_id = %s", (alert_id,)
            )


def log_audit(
    user_id: int | None,
    action: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    metadata: dict | None = None,
    ip_address: str | None = None,
) -> None:
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO audit_logs (user_id, action, resource_type, resource_id, metadata, ip_address)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (user_id, action, resource_type, resource_id, json.dumps(metadata) if metadata else None, ip_address),
        )


def log_notification(user_id: int, subject: str, body: str, alert_id: int | None = None, status: str = "logged") -> None:
    with get_db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            INSERT INTO notification_log (user_id, alert_id, subject, body, status)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user_id, alert_id, subject, body, status),
        )
