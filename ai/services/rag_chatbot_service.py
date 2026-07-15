"""Core RAG logic: embed the question, retrieve relevant job postings,
build a grounded prompt, and generate an answer - with citations back to
the postings actually used, so an answer's provenance is checkable
instead of trusted blindly.

Providers/store are accepted as optional parameters (falling back to the
configured registry) so tests can inject fakes without needing real API
keys or network access.
"""
from ai.models.schemas import ChatSource
from ai.prompts.rag_chatbot import build_context, build_messages
from ai.providers.base import ChatProvider, EmbeddingProvider
from ai.providers.registry import get_chat_provider, get_embedding_provider
from ai.services.conversation_store import append_turn, get_history, new_conversation_id
from ai.vectorstore.base import VectorStore
from ai.vectorstore.registry import get_vector_store
from utils.exceptions import DataValidationError
from utils.logger import logger

_TOP_K = 5


def answer_question(
    message: str,
    conversation_id: str | None = None,
    chat_provider: ChatProvider | None = None,
    embedding_provider: EmbeddingProvider | None = None,
    vector_store: VectorStore | None = None,
) -> dict:
    message = message.strip()
    if not message:
        raise DataValidationError("message must not be empty")

    conversation_id = conversation_id or new_conversation_id()
    history = get_history(conversation_id)

    embedder = embedding_provider or get_embedding_provider()
    query_vector = embedder.embed([message])[0]

    store = vector_store or get_vector_store(dimensions=embedder.dimensions)
    matches = store.query(query_vector, top_k=_TOP_K)

    context = build_context(matches)
    messages = build_messages(context, history, message)

    chat = chat_provider or get_chat_provider()
    result = chat.generate(messages)

    logger.info(
        "[ai-chat] conversation=%s prompt_tokens=%s completion_tokens=%s",
        conversation_id, result.prompt_tokens, result.completion_tokens,
    )

    append_turn(conversation_id, "user", message)
    append_turn(conversation_id, "assistant", result.text)

    sources = [
        ChatSource(
            job_id=match.metadata.get("job_id", match.id),
            position=match.metadata.get("position"),
            company=match.metadata.get("company"),
            score=match.score,
        )
        for match in matches
    ]

    return {
        "answer": result.text,
        "sources": sources,
        "conversation_id": conversation_id,
        "prompt_tokens": result.prompt_tokens,
        "completion_tokens": result.completion_tokens,
    }
