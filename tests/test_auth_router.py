import uuid

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def _unique_email() -> str:
    return f"test-{uuid.uuid4().hex[:12]}@example.com"


def _register_payload(email: str, password: str = "SuperSecret123", **overrides) -> dict:
    payload = {
        "first_name": "Test",
        "last_name": "User",
        "email": email,
        "password": password,
        "confirm_password": password,
        "terms_accepted": True,
    }
    payload.update(overrides)
    return payload


def _register(email: str, password: str = "SuperSecret123") -> dict:
    response = client.post("/api/v1/auth/register", json=_register_payload(email, password))
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
    response = client.post("/api/v1/auth/register", json=_register_payload(email, "AnotherPass123"))
    assert response.status_code == 409


def test_register_rejects_short_password(use_test_db):
    response = client.post("/api/v1/auth/register", json=_register_payload(_unique_email(), "short", confirm_password="short"))
    assert response.status_code == 422


def test_register_rejects_mismatched_confirm_password(use_test_db):
    response = client.post(
        "/api/v1/auth/register",
        json=_register_payload(_unique_email(), "SuperSecret123", confirm_password="Different123"),
    )
    assert response.status_code == 422


def test_register_rejects_unaccepted_terms(use_test_db):
    response = client.post("/api/v1/auth/register", json=_register_payload(_unique_email(), terms_accepted=False))
    assert response.status_code == 422


def test_register_maps_country_and_job_title_into_profile(use_test_db):
    email = _unique_email()
    tokens = client.post(
        "/api/v1/auth/register",
        json=_register_payload(email, country="Canada", job_title="Data Engineer"),
    ).json()

    response = client.get("/api/v1/auth/me/profile", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert response.status_code == 200
    body = response.json()
    assert body["location"] == "Canada"
    assert body["headline"] == "Data Engineer"


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


def test_login_remember_me_off_issues_shorter_refresh_token(use_test_db):
    import jwt as pyjwt

    from config.settings import settings

    email = _unique_email()
    _register(email)

    remembered = client.post("/api/v1/auth/login", json={"email": email, "password": "SuperSecret123", "remember_me": True})
    not_remembered = client.post("/api/v1/auth/login", json={"email": email, "password": "SuperSecret123", "remember_me": False})

    remembered_exp = pyjwt.decode(remembered.json()["refresh_token"], settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])["exp"]
    short_exp = pyjwt.decode(not_remembered.json()["refresh_token"], settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])["exp"]
    assert short_exp < remembered_exp


def test_forgot_password_always_returns_200_regardless_of_email(use_test_db):
    known = client.post("/api/v1/auth/forgot-password", json={"email": _unique_email()})
    unknown = client.post("/api/v1/auth/forgot-password", json={"email": "definitely-not-registered@example.com"})
    assert known.status_code == 200
    assert unknown.status_code == 200
    assert known.json() == unknown.json()


def test_forgot_and_reset_password_flow(use_test_db, monkeypatch):
    import auth.router as auth_router_module

    email = _unique_email()
    _register(email)

    # secrets.token_urlsafe is mocked to a known value so the test can use
    # the same raw token the endpoint generated, without needing to scrape
    # it out of a real email.
    monkeypatch.setattr(auth_router_module.secrets, "token_urlsafe", lambda n: "known-reset-token")

    response = client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert response.status_code == 200

    reset = client.post("/api/v1/auth/reset-password", json={"token": "known-reset-token", "new_password": "BrandNewPass123"})
    assert reset.status_code == 200

    old_login = client.post("/api/v1/auth/login", json={"email": email, "password": "SuperSecret123"})
    assert old_login.status_code == 401

    new_login = client.post("/api/v1/auth/login", json={"email": email, "password": "BrandNewPass123"})
    assert new_login.status_code == 200


def test_reset_password_rejects_invalid_token(use_test_db):
    response = client.post("/api/v1/auth/reset-password", json={"token": "not-a-real-token", "new_password": "WhateverPass123"})
    assert response.status_code == 400


def test_change_password_requires_correct_current_password(use_test_db):
    email = _unique_email()
    tokens = _register(email)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    wrong = client.patch("/api/v1/auth/me/password", json={"current_password": "WrongOne123", "new_password": "NewPass456"}, headers=headers)
    assert wrong.status_code == 401

    right = client.patch(
        "/api/v1/auth/me/password", json={"current_password": "SuperSecret123", "new_password": "NewPass456"}, headers=headers
    )
    assert right.status_code == 200

    old_login = client.post("/api/v1/auth/login", json={"email": email, "password": "SuperSecret123"})
    assert old_login.status_code == 401
    new_login = client.post("/api/v1/auth/login", json={"email": email, "password": "NewPass456"})
    assert new_login.status_code == 200
