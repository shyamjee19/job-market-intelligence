"""Pinecone-backed VectorStore - https://docs.pinecone.io/guides/get-started/quickstart

Built against Pinecone's documented Python SDK (v5, package name
"pinecone") but not yet exercised against a live Pinecone account - there
was no API key available while building this (same situation Adzuna was
in before it got verified). Worth a smoke test the first time
PINECONE_API_KEY is set for real: run ai/services/rag_indexer.py and
confirm `pc.describe_index_stats()` shows the expected vector count.
"""
from pinecone import Pinecone, ServerlessSpec

from ai.vectorstore.base import VectorMatch, VectorRecord, VectorStore
from config.settings import settings
from utils.exceptions import APIRequestError
from utils.logger import logger

_TEXT_METADATA_KEY = "_text"  # Pinecone has no separate "document body" field - text rides in metadata.


class PineconeVectorStore(VectorStore):
    name = "pinecone"

    def __init__(self, dimensions: int):
        if not settings.PINECONE_API_KEY:
            raise APIRequestError("PINECONE_API_KEY is not set")

        self._pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self._index_name = settings.PINECONE_INDEX_NAME
        self._ensure_index(dimensions)
        self._index = self._pc.Index(self._index_name)

    def _ensure_index(self, dimensions: int) -> None:
        existing = {idx["name"] for idx in self._pc.list_indexes()}
        if self._index_name in existing:
            return

        logger.info("Creating Pinecone index '%s' (dimensions=%d)", self._index_name, dimensions)
        self._pc.create_index(
            name=self._index_name,
            dimension=dimensions,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )

    def upsert(self, records: list[VectorRecord]) -> None:
        vectors = [
            {
                "id": record.id,
                "values": record.vector,
                "metadata": {**record.metadata, _TEXT_METADATA_KEY: record.text},
            }
            for record in records
        ]
        self._index.upsert(vectors=vectors)

    def query(self, vector: list[float], top_k: int = 5) -> list[VectorMatch]:
        response = self._index.query(vector=vector, top_k=top_k, include_metadata=True)
        matches = []
        for match in response.matches:
            metadata = dict(match.metadata or {})
            text = metadata.pop(_TEXT_METADATA_KEY, "")
            matches.append(VectorMatch(id=match.id, score=match.score, text=text, metadata=metadata))
        return matches
