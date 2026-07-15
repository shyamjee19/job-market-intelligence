from fastapi.testclient import TestClient

import ai.router as ai_router_module
from ai.services import ai_tools_service
from api.main import app
from config.settings import settings
from utils.rate_limiter import reset as reset_rate_limit

client = TestClient(app)

# TestClient always reports its connection as this fixed host - the router
# reads request.client.host (raw ASGI connection info, not X-Forwarded-For
# or similar headers), so every request in this file shares one rate-limit
# bucket keyed on this string. Tests that care about the limit reset it
# explicitly rather than relying on execution order across the file.
_TEST_CLIENT_ID = "testclient"


def _fake_answer_question(message, conversation_id=None):
    return {
        "answer": "fake answer",
        "sources": [],
        "conversation_id": conversation_id or "fake-conversation-id",
        "prompt_tokens": 10,
        "completion_tokens": 5,
    }


def test_chat_endpoint_returns_answer(monkeypatch):
    monkeypatch.setattr(ai_router_module, "answer_question", _fake_answer_question)
    reset_rate_limit("ai-chat", _TEST_CLIENT_ID)

    response = client.post("/api/v1/ai/chat", json={"message": "What skills are trending?"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "fake answer"
    assert body["conversation_id"] == "fake-conversation-id"


def test_chat_endpoint_rejects_empty_message():
    response = client.post("/api/v1/ai/chat", json={"message": ""})
    assert response.status_code == 422


def test_chat_endpoint_rejects_overlong_message():
    response = client.post("/api/v1/ai/chat", json={"message": "x" * (settings.AI_MAX_MESSAGE_LENGTH + 1)})
    assert response.status_code == 422


def test_chat_endpoint_rate_limits_after_threshold(monkeypatch):
    monkeypatch.setattr(ai_router_module, "answer_question", _fake_answer_question)
    reset_rate_limit("ai-chat", _TEST_CLIENT_ID)

    for _ in range(settings.AI_RATE_LIMIT_PER_MINUTE):
        response = client.post("/api/v1/ai/chat", json={"message": "hi"})
        assert response.status_code == 200

    response = client.post("/api/v1/ai/chat", json={"message": "hi"})
    assert response.status_code == 429


def _register_and_login(use_test_db) -> str:
    import uuid

    email = f"test-{uuid.uuid4().hex[:12]}@example.com"
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
    return response.json()["access_token"]


def _fake_tool_result(*args, **kwargs) -> dict:
    return {"summary": "fake tool summary", "data": {"ok": True}}


def test_ai_tool_endpoints_require_authentication():
    assert client.post("/api/v1/ai/tools/resume-analyzer", json={"resume_text": "x" * 60}).status_code == 401
    assert client.post("/api/v1/ai/tools/career-advisor", json={"current_skills": "python", "goal": "backend"}).status_code == 401
    assert client.post("/api/v1/ai/tools/skill-gap", json={"current_skills": "python", "target_role": "backend"}).status_code == 401
    assert client.post("/api/v1/ai/tools/salary-insights", json={}).status_code == 401
    assert client.get("/api/v1/ai/tools/job-recommendations").status_code == 401
    assert client.post("/api/v1/ai/tools/interview-prep", json={"role": "backend"}).status_code == 401


def test_resume_analyzer_endpoint_returns_tool_response(use_test_db, monkeypatch):
    monkeypatch.setattr(ai_tools_service, "analyze_resume", _fake_tool_result)
    token = _register_and_login(use_test_db)

    response = client.post(
        "/api/v1/ai/tools/resume-analyzer",
        json={"resume_text": "x" * 60},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["summary"] == "fake tool summary"


def test_resume_analyzer_endpoint_rejects_short_resume(use_test_db):
    token = _register_and_login(use_test_db)
    response = client.post(
        "/api/v1/ai/tools/resume-analyzer",
        json={"resume_text": "too short"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422


def test_job_recommendations_endpoint_uses_profile_skills(use_test_db, monkeypatch):
    captured = {}

    def _fake_job_recommendations(skills, *args, **kwargs):
        captured["skills"] = skills
        return {"summary": "fake", "data": {"jobs": []}}

    monkeypatch.setattr(ai_tools_service, "job_recommendations", _fake_job_recommendations)
    token = _register_and_login(use_test_db)
    headers = {"Authorization": f"Bearer {token}"}

    client.put("/api/v1/users/me/profile", json={"skills": ["python", "sql"]}, headers=headers)
    response = client.get("/api/v1/ai/tools/job-recommendations", headers=headers)

    assert response.status_code == 200
    assert captured["skills"] == ["python", "sql"]


def test_ai_tool_endpoint_returns_503_on_provider_failure(use_test_db, monkeypatch):
    def _boom(*args, **kwargs):
        raise RuntimeError("provider exploded")

    monkeypatch.setattr(ai_tools_service, "interview_prep", _boom)
    token = _register_and_login(use_test_db)

    response = client.post(
        "/api/v1/ai/tools/interview-prep",
        json={"role": "Data Engineer"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 503
