import uuid

from fastapi.testclient import TestClient

from api.main import app
from database.users_repository import set_user_role

client = TestClient(app)


def _unique_email() -> str:
    return f"test-{uuid.uuid4().hex[:12]}@example.com"


def _register(email: str) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Test",
            "last_name": "User",
            "email": email,
            "password": "SuperSecret123",
            "confirm_password": "SuperSecret123",
            "terms_accepted": True,
        },
    )
    return response.json()


def _register_admin() -> dict:
    tokens = _register(_unique_email())
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}).json()
    set_user_role(me["user_id"], "admin")

    # Re-login: the access token already issued still carries role="user"
    # in its payload (JWTs are immutable once signed), so a fresh token
    # is needed to pick up the promotion.
    login = client.post("/api/v1/auth/login", json={"email": me["email"], "password": "SuperSecret123"})
    return login.json()


def test_admin_stats_requires_admin_role(use_test_db):
    tokens = _register(_unique_email())
    response = client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert response.status_code == 403


def test_admin_stats_accessible_to_admin(use_test_db):
    tokens = _register_admin()
    response = client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert response.status_code == 200
    assert "total_users" in response.json()


def test_admin_user_list_excludes_password_hash(use_test_db):
    tokens = _register_admin()
    response = client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert response.status_code == 200
    for user in response.json()["items"]:
        assert "hashed_password" not in user


def test_admin_can_change_user_role(use_test_db):
    admin_tokens = _register_admin()
    target_tokens = _register(_unique_email())
    target_user_id = client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {target_tokens['access_token']}"}
    ).json()["user_id"]

    response = client.patch(
        f"/api/v1/admin/users/{target_user_id}/role",
        json={"role": "admin"},
        headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
    )
    assert response.status_code == 204


def test_admin_audit_logs_accessible(use_test_db):
    tokens = _register_admin()
    response = client.get("/api/v1/admin/audit-logs", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert response.status_code == 200
    assert response.json()["total"] >= 1  # at least the admin's own register/login
