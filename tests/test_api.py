import pytest
from fastapi.testclient import TestClient

from api.main import app
from database.connection import get_connection
from utils.exceptions import DatabaseError


@pytest.fixture(scope="module", autouse=True)
def _require_database():
    try:
        conn = get_connection()
        conn.close()
    except DatabaseError as e:
        pytest.skip(f"No database available: {e}")


client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_list_jobs_shape():
    response = client.get("/api/jobs", params={"page_size": 5})
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"items", "total", "page", "page_size"}
    assert len(body["items"]) <= 5


def test_get_job_not_found():
    response = client.get("/api/jobs/999999999")
    assert response.status_code == 404


def test_stats_summary_shape():
    response = client.get("/api/stats/summary")
    assert response.status_code == 200
    body = response.json()
    assert "total_jobs" in body


def test_top_companies_shape():
    response = client.get("/api/stats/top-companies", params={"limit": 3})
    assert response.status_code == 200
    assert len(response.json()) <= 3


def test_companies_endpoint():
    response = client.get("/api/companies", params={"limit": 3})
    assert response.status_code == 200
    assert len(response.json()) <= 3


def test_skills_endpoint():
    response = client.get("/api/skills", params={"limit": 3})
    assert response.status_code == 200
    assert len(response.json()) <= 3


def test_sources_endpoint():
    response = client.get("/api/stats/sources")
    assert response.status_code == 200


def test_jobs_csv_export():
    response = client.get("/api/jobs/export.csv", params={"page_size": 5})
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.text.splitlines()[0].startswith("id,source,position")
