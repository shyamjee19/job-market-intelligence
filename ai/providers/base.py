"""Provider interfaces the rest of the ai/ module codes against - never a
concrete SDK. Swapping OpenAI for Claude/Azure/Ollama, or changing the
embedding model, means adding a class here and a line in registry.py;
nothing in ai/services/ changes.

Chat and embeddings are separate interfaces on purpose: Anthropic has no
embeddings API at all, so "Claude for chat" still needs some other
provider to turn text into vectors - config/settings.py's
AI_CHAT_PROVIDER and AI_EMBEDDING_PROVIDER are independent for exactly
this reason.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ChatMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class ChatResult:
    text: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class ChatProvider(ABC):
    """Turns a conversation into a completion."""

    name: str

    @abstractmethod
    def generate(self, messages: list[ChatMessage], temperature: float = 0.2) -> ChatResult:
        raise NotImplementedError


class EmbeddingProvider(ABC):
    """Turns text into vectors for the RAG vector store."""

    name: str
    dimensions: int

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError
