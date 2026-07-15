import pytest

from ai.providers.base import ChatMessage, ChatProvider, ChatResult, EmbeddingProvider
from ai.services import conversation_store
from ai.services.rag_chatbot_service import answer_question
from ai.vectorstore.base import VectorMatch, VectorRecord, VectorStore
from utils.exceptions import DataValidationError


class FakeEmbeddingProvider(EmbeddingProvider):
    name = "fake"
    dimensions = 3

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0, 0.0] for _ in texts]


class FakeChatProvider(ChatProvider):
    name = "fake"

    def __init__(self):
        self.received_messages: list[list[ChatMessage]] = []

    def generate(self, messages: list[ChatMessage], temperature: float = 0.2) -> ChatResult:
        self.received_messages.append(messages)
        return ChatResult(text="Python is trending.", prompt_tokens=42, completion_tokens=7)


class FakeVectorStore(VectorStore):
    name = "fake"

    def upsert(self, records: list[VectorRecord]) -> None:
        raise NotImplementedError

    def query(self, vector: list[float], top_k: int = 5) -> list[VectorMatch]:
        return [
            VectorMatch(
                id="123",
                score=0.95,
                text="Position: Backend Engineer at Acme.",
                metadata={"job_id": "123", "company": "Acme", "position": "Backend Engineer"},
            )
        ]


def test_answer_question_returns_grounded_answer_with_sources():
    chat = FakeChatProvider()
    result = answer_question(
        "What skills are trending?",
        chat_provider=chat,
        embedding_provider=FakeEmbeddingProvider(),
        vector_store=FakeVectorStore(),
    )

    assert result["answer"] == "Python is trending."
    assert result["prompt_tokens"] == 42
    assert result["completion_tokens"] == 7
    assert len(result["sources"]) == 1
    assert result["sources"][0].company == "Acme"
    assert result["sources"][0].position == "Backend Engineer"


def test_answer_question_rejects_empty_message():
    with pytest.raises(DataValidationError):
        answer_question(
            "   ",
            chat_provider=FakeChatProvider(),
            embedding_provider=FakeEmbeddingProvider(),
            vector_store=FakeVectorStore(),
        )


def test_answer_question_persists_conversation_history():
    chat = FakeChatProvider()
    conversation_id = "test-conversation-history"

    answer_question(
        "first question",
        conversation_id=conversation_id,
        chat_provider=chat,
        embedding_provider=FakeEmbeddingProvider(),
        vector_store=FakeVectorStore(),
    )
    answer_question(
        "second question",
        conversation_id=conversation_id,
        chat_provider=chat,
        embedding_provider=FakeEmbeddingProvider(),
        vector_store=FakeVectorStore(),
    )

    history = conversation_store.get_history(conversation_id)
    assert [m.content for m in history] == [
        "first question", "Python is trending.", "second question", "Python is trending.",
    ]

    # the second call's prompt should include the first turn's history
    second_call_messages = chat.received_messages[1]
    assert any(m.content == "first question" for m in second_call_messages)


def test_answer_question_generates_new_conversation_id_when_none_given():
    result = answer_question(
        "a question",
        chat_provider=FakeChatProvider(),
        embedding_provider=FakeEmbeddingProvider(),
        vector_store=FakeVectorStore(),
    )
    assert result["conversation_id"]
