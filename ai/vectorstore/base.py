from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class VectorRecord:
    id: str
    vector: list[float]
    text: str
    metadata: dict = field(default_factory=dict)


@dataclass
class VectorMatch:
    id: str
    score: float
    text: str
    metadata: dict


class VectorStore(ABC):
    """Swappable RAG storage/retrieval backend. ai/services/ codes only
    against this interface, so switching from the in-memory default to
    Pinecone (or later, Qdrant/Chroma/LangChain/LlamaIndex) is a
    registry.py change, not a rewrite of the chatbot logic."""

    name: str

    @abstractmethod
    def upsert(self, records: list[VectorRecord]) -> None:
        raise NotImplementedError

    @abstractmethod
    def query(self, vector: list[float], top_k: int = 5) -> list[VectorMatch]:
        raise NotImplementedError
