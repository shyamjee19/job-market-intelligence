import uuid

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def _unique_email() -> str:
    return f"test-{uuid.uuid4().hex[:12]}@example.com"


def _register(email: str, password: str = "SuperSecret123") -> dict:
    response = client.post("/api/v1/auth/register", json={"email": email, "password": password, "full_name": "Test User"})
    assert response.status_code == 201, response.text
    return response.json()


def test_register_returns_tokens(use_test_db):
    tokens = _register(_unique_email())
    assert tokens["token_type"] == "bearer"
    assert tokens["access_token"]
    assert tokens["refresh_token"]


def test_register_duplicate_email_is_rejected(use_test_db):
    email = _unique_email()
    _register(email)
    response = client.post("/api/v1/auth/register", json={"email": email, "password": "AnotherPass123"})
    assert response.status_code == 409


def test_register_rejects_short_password(use_test_db):
    response = client.post("/api/v1/auth/register", json={"email": _unique_email(), "password": "short"})
    assert response.status_code == 422


def test_login_success(use_test_db):
    email = _unique_email()
    _register(email, password="SuperSecret123")

    response = client.post("/api/v1/auth/login", json={"email": email, "password": "SuperSecret123"})
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_wrong_password_rejected(use_test_db):
    email = _unique_email()
    _register(email, password="SuperSecret123")

    response = client.post("/api/v1/auth/login", json={"email": email, "password": "WrongPassword"})
    assert response.status_code == 401


def test_login_unknown_email_rejected(use_test_db):
    response = client.post("/api/v1/auth/login", json={"email": _unique_email(), "password": "whatever123"})
    assert response.status_code == 401


def test_me_requires_authentication(use_test_db):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_returns_current_user(use_test_db):
    email = _unique_email()
    tokens = _register(email)

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert response.status_code == 200
    assert response.json()["email"] == email
    assert response.json()["role"] == "user"


def test_me_rejects_garbage_token(use_test_db):
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


def test_refresh_issues_new_tokens_and_revokes_old(use_test_db):
    tokens = _register(_unique_email())

    refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 200
    assert refreshed.json()["access_token"] != tokens["access_token"]

    reused = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert reused.status_code == 401


def test_logout_revokes_refresh_token(use_test_db):
    tokens = _register(_unique_email())

    logout_response = client.post("/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    assert logout_response.status_code == 204

    refresh_response = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refresh_response.status_code == 401


def test_admin_endpoint_forbidden_for_regular_user(use_test_db):
    tokens = _register(_unique_email())
    response = client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert response.status_code == 403
