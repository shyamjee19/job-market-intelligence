import pytest

from database.connection import get_connection
from database.repository import count_jobs, upsert_jobs


@pytest.fixture(autouse=True)
def _clean_tables(test_db):
    with get_connection(dbname=test_db) as conn:
        with conn.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE fact_jobs, dim_company, dim_location, dim_skill, dim_source CASCADE")
        conn.commit()


def make_job(external_id="1", **overrides):
    base = {
        "external_id": external_id,
        "company": "Acme",
        "position": "Backend Engineer",
        "location": "Remote",
        "remote_type": "remote",
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
    upsert_jobs("remoteok", [make_job("1"), make_job("2")], dbname=test_db)
    assert count_jobs(dbname=test_db) == 2


def test_upsert_updates_existing_job_on_conflict(test_db):
    upsert_jobs("remoteok", [make_job("1", company="Acme")], dbname=test_db)
    upsert_jobs("remoteok", [make_job("1", company="Acme Renamed")], dbname=test_db)

    assert count_jobs(dbname=test_db) == 1

    with get_connection(dbname=test_db) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT dc.company_name FROM fact_jobs f JOIN dim_company dc ON dc.company_key = f.company_key"
            )
            assert cursor.fetchone()[0] == "Acme Renamed"


def test_same_external_id_different_sources_stay_distinct(test_db):
    upsert_jobs("remoteok", [make_job("1")], dbname=test_db)
    upsert_jobs("arbeitnow", [make_job("1")], dbname=test_db)
    assert count_jobs(dbname=test_db) == 2


def test_upsert_replaces_skill_bridge(test_db):
    upsert_jobs("remoteok", [make_job("1", tags=["python", "django"])], dbname=test_db)
    upsert_jobs("remoteok", [make_job("1", tags=["rust"])], dbname=test_db)

    with get_connection(dbname=test_db) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT sk.skill_name FROM bridge_job_skill bjs
                JOIN dim_skill sk ON sk.skill_key = bjs.skill_key
                JOIN fact_jobs f ON f.job_key = bjs.job_key
                WHERE f.external_id = '1'
                """
            )
            skills = {row[0] for row in cursor.fetchall()}
            assert skills == {"rust"}
