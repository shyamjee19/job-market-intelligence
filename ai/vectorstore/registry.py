from ai.vectorstore.base import VectorStore
from config.settings import settings


def get_vector_store(dimensions: int) -> VectorStore:
    """VECTOR_STORE_PROVIDER defaults to "memory" (no account needed).
    Set it to "pinecone" once PINECONE_API_KEY is configured."""
    provider = settings.VECTOR_STORE_PROVIDER

    if provider == "memory":
        from ai.vectorstore.memory_store import InMemoryVectorStore
        return InMemoryVectorStore()
    if provider == "pinecone":
        from ai.vectorstore.pinecone_store import PineconeVectorStore
        return PineconeVectorStore(dimensions=dimensions)

    raise ValueError(f"Unknown VECTOR_STORE_PROVIDER '{provider}'. Expected one of: memory, pinecone")
