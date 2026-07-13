import pytest

from database.connection import get_connection
from database.repository import count_jobs, upsert_jobs


@pytest.fixture(autouse=True)
def _clean_jobs_table(test_db):
    with get_connection(dbname=test_db) as conn:
        with conn.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE jobs")
        conn.commit()


def make_job(job_id=1, **overrides):
    base = {
        "job_id": job_id,
        "company": "Acme",
        "position": "Backend Engineer",
        "location": "Remote",
        "salary_min": 70000,
        "salary_max": 90000,
        "date_posted": None,
        "tags": ["python"],
        "job_url": "https://example.com/1",
        "apply_url": "https://example.com/apply/1",
        "description": "Build things.",
    }
    base.update(overrides)
    return base


def test_upsert_inserts_new_jobs(test_db):
    upsert_jobs([make_job(1), make_job(2)], dbname=test_db)
    assert count_jobs(dbname=test_db) == 2


def test_upsert_updates_existing_job_on_conflict(test_db):
    upsert_jobs([make_job(1, company="Acme")], dbname=test_db)
    upsert_jobs([make_job(1, company="Acme Renamed")], dbname=test_db)

    assert count_jobs(dbname=test_db) == 1

    with get_connection(dbname=test_db) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT company FROM jobs WHERE job_id = 1")
            assert cursor.fetchone()[0] == "Acme Renamed"
