"""In-memory conversation history, keyed by conversation_id.

Dev-grade on purpose: history is lost on process restart and doesn't
share across multiple API workers. A real deployment would back this
with Postgres or Redis - noted here rather than silently assumed, since
"conversation history" was an explicit requirement.
"""
import uuid
from collections import defaultdict

from ai.providers.base import ChatMessage

_MAX_HISTORY_TURNS = 10

_conversations: dict[str, list[ChatMessage]] = defaultdict(list)


def new_conversation_id() -> str:
    return str(uuid.uuid4())


def get_history(conversation_id: str) -> list[ChatMessage]:
    return list(_conversations[conversation_id][-_MAX_HISTORY_TURNS:])


def append_turn(conversation_id: str, role: str, content: str) -> None:
    _conversations[conversation_id].append(ChatMessage(role=role, content=content))
