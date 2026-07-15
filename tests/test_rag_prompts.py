from ai.prompts.rag_chatbot import SYSTEM_PROMPT, build_context, build_messages
from ai.providers.base import ChatMessage
from ai.vectorstore.base import VectorMatch


def test_build_context_formats_numbered_matches():
    matches = [
        VectorMatch(id="1", score=0.9, text="Backend Engineer at Acme", metadata={}),
        VectorMatch(id="2", score=0.8, text="Data Scientist at Beta", metadata={}),
    ]
    context = build_context(matches)
    assert "[1] Backend Engineer at Acme" in context
    assert "[2] Data Scientist at Beta" in context


def test_build_context_handles_no_matches():
    assert "no matching" in build_context([]).lower()


def test_build_messages_includes_system_context_history_and_question():
    history = [ChatMessage(role="user", content="earlier question")]
    messages = build_messages(context="some context", history=history, question="new question")

    assert messages[0].role == "system"
    assert messages[0].content == SYSTEM_PROMPT
    assert messages[1].role == "system"
    assert "some context" in messages[1].content
    assert messages[2] == history[0]
    assert messages[-1] == ChatMessage(role="user", content="new question")
