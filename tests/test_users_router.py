import uuid

import pytest
from fastapi.testclient import TestClient

from api.main import app
from database.connection import get_connection
from database.repository import upsert_jobs

client = TestClient(app)


def _unique_email() -> str:
    return f"test-{uuid.uuid4().hex[:12]}@example.com"


def _register_and_login(use_test_db) -> tuple[dict, str]:
    email = _unique_email()
    response = client.post("/api/v1/auth/register", json={"email": email, "password": "SuperSecret123"})
    tokens = response.json()
    return tokens, tokens["access_token"]


@pytest.fixture
def seeded_job(use_test_db):
    """Inserts one job into the isolated test database and returns its
    (job_key, company_name) so saved-jobs/favorites tests have something
    real to point at."""
    upsert_jobs(
        "remoteok",
        [
            {
                "external_id": "test-job-1",
                "company": "Acme Test Co",
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
        ],
        dbname=use_test_db,
    )
    with get_connection(dbname=use_test_db) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT job_key FROM fact_jobs WHERE external_id = 'test-job-1'")
            job_key = cursor.fetchone()[0]
    return job_key, "Acme Test Co"


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_saved_jobs_requires_auth(use_test_db, seeded_job):
    job_key, _ = seeded_job
    response = client.post(f"/api/v1/users/me/saved-jobs/{job_key}")
    assert response.status_code == 401


def test_save_list_and_remove_job(use_test_db, seeded_job):
    job_key, _ = seeded_job
    _, token = _register_and_login(use_test_db)
    headers = _auth_header(token)

    add_response = client.post(f"/api/v1/users/me/saved-jobs/{job_key}", headers=headers)
    assert add_response.status_code == 204

    list_response = client.get("/api/v1/users/me/saved-jobs", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["position"] == "Backend Engineer"

    remove_response = client.delete(f"/api/v1/users/me/saved-jobs/{job_key}", headers=headers)
    assert remove_response.status_code == 204

    empty_list = client.get("/api/v1/users/me/saved-jobs", headers=headers)
    assert empty_list.json() == []


def test_save_nonexistent_job_returns_404(use_test_db):
    _, token = _register_and_login(use_test_db)
    response = client.post("/api/v1/users/me/saved-jobs/999999999", headers=_auth_header(token))
    assert response.status_code == 404


def test_favorite_list_and_unfavorite_company(use_test_db, seeded_job):
    _, company_name = seeded_job
    _, token = _register_and_login(use_test_db)
    headers = _auth_header(token)

    add_response = client.post(f"/api/v1/users/me/favorites/{company_name}", headers=headers)
    assert add_response.status_code == 204

    list_response = client.get("/api/v1/users/me/favorites", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()[0]["company_name"] == company_name

    remove_response = client.delete(f"/api/v1/users/me/favorites/{company_name}", headers=headers)
    assert remove_response.status_code == 204
    assert client.get("/api/v1/users/me/favorites", headers=headers).json() == []


def test_favorite_unknown_company_returns_404(use_test_db):
    _, token = _register_and_login(use_test_db)
    response = client.post("/api/v1/users/me/favorites/Not%20A%20Real%20Company", headers=_auth_header(token))
    assert response.status_code == 404


def test_create_list_and_delete_alert(use_test_db):
    _, token = _register_and_login(use_test_db)
    headers = _auth_header(token)

    create_response = client.post(
        "/api/v1/users/me/alerts",
        json={"name": "Python jobs", "keywords": "python", "frequency": "daily"},
        headers=headers,
    )
    assert create_response.status_code == 201
    alert_id = create_response.json()["alert_id"]

    list_response = client.get("/api/v1/users/me/alerts", headers=headers)
    assert len(list_response.json()) == 1

    delete_response = client.delete(f"/api/v1/users/me/alerts/{alert_id}", headers=headers)
    assert delete_response.status_code == 204
    assert client.get("/api/v1/users/me/alerts", headers=headers).json() == []


def test_update_profile(use_test_db):
    _, token = _register_and_login(use_test_db)
    headers = _auth_header(token)

    response = client.put(
        "/api/v1/users/me/profile",
        json={"headline": "Senior Engineer", "skills": ["python", "sql"]},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["headline"] == "Senior Engineer"
    assert response.json()["skills"] == ["python", "sql"]
