from fastapi.testclient import TestClient

import ai.router as ai_router_module
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
