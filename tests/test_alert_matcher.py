import uuid

import pytest

from database.connection import get_connection
from database.repository import upsert_jobs
from database.users_queries import get_alert
from database.users_repository import create_alert, create_user
from jobs.alert_matcher import check_all_alerts


@pytest.fixture(autouse=True)
def _clean_tables(use_test_db):
    # This suite asserts exact notification counts ("second run finds 0
    # new matches") - a leftover active alert from a previous pytest
    # invocation (the test database persists across separate runs,
    # unlike an in-process fixture) could pick up this test's freshly
    # seeded job and break that assumption, so start every test from a
    # clean slate rather than just using unique emails/ids.
    with get_connection(dbname=use_test_db) as conn:
        with conn.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE job_alerts, notification_log, users, fact_jobs, dim_company RESTART IDENTITY CASCADE")
        conn.commit()


def _unique_email() -> str:
    return f"alert-test-{uuid.uuid4().hex[:12]}@example.com"


def _seed_job(external_id: str, position: str, tags: list[str]):
    upsert_jobs(
        "remoteok",
        [
            {
                "external_id": external_id,
                "company": "Acme Test Co",
                "position": position,
                "location": "Remote",
                "remote_type": "remote",
                "salary_min": 70000,
                "salary_max": 90000,
                "date_posted": None,
                "tags": tags,
                "job_url": "https://example.com/1",
                "apply_url": "https://example.com/apply/1",
                "description": "Build things.",
            }
        ],
    )


def test_matching_alert_gets_notified(use_test_db):
    _seed_job(f"alert-test-1-{uuid.uuid4().hex[:8]}", "Python Backend Engineer", ["python"])
    user = create_user(email=_unique_email(), hashed_password="x")
    create_alert(user["user_id"], name="Python roles", keywords="Python", frequency="daily")

    results = check_all_alerts()

    assert results["notifications_sent"] >= 1


def test_alert_advances_high_water_mark_and_does_not_renotify(use_test_db):
    _seed_job(f"alert-test-2-{uuid.uuid4().hex[:8]}", "Rust Engineer", ["rust"])
    user = create_user(email=_unique_email(), hashed_password="x")
    alert = create_alert(user["user_id"], name="Rust roles", keywords="Rust", frequency="daily")

    first_run = check_all_alerts()
    assert first_run["notifications_sent"] >= 1

    updated_alert = get_alert(alert["alert_id"], user["user_id"])
    assert updated_alert["last_notified_job_key"] is not None
    assert updated_alert["last_checked_at"] is not None

    # No new postings for any alert since the last check (this test's own
    # alert included) - re-running must not notify about the same job again.
    second_run = check_all_alerts()
    assert second_run["notifications_sent"] == 0


def test_alert_with_no_matches_is_still_marked_checked(use_test_db):
    user = create_user(email=_unique_email(), hashed_password="x")
    alert = create_alert(user["user_id"], name="Nonexistent tech", keywords="quantumfoobar", frequency="daily")

    check_all_alerts()

    updated_alert = get_alert(alert["alert_id"], user["user_id"])
    assert updated_alert["last_checked_at"] is not None
