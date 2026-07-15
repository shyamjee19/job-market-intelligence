"""Default vector store: no account, no server, just numpy cosine
similarity over vectors persisted to a local JSON file. Fine at the data
volumes this project deals with (hundreds to low thousands of job
postings) - not meant to scale past that, which is exactly the point
where you'd flip VECTOR_STORE_PROVIDER to "pinecone" instead.
"""
import json
import os

import numpy as np

from ai.vectorstore.base import VectorMatch, VectorRecord, VectorStore

DEFAULT_STORE_PATH = "data/ai/memory_vector_store.json"


class InMemoryVectorStore(VectorStore):
    name = "memory"

    def __init__(self, path: str = DEFAULT_STORE_PATH):
        self._path = path
        self._records: dict[str, VectorRecord] = {}
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self._path):
            return
        with open(self._path, "r", encoding="utf-8") as file:
            raw = json.load(file)
        self._records = {
            r["id"]: VectorRecord(id=r["id"], vector=r["vector"], text=r["text"], metadata=r["metadata"])
            for r in raw
        }

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as file:
            json.dump(
                [
                    {"id": r.id, "vector": r.vector, "text": r.text, "metadata": r.metadata}
                    for r in self._records.values()
                ],
                file,
            )

    def upsert(self, records: list[VectorRecord]) -> None:
        for record in records:
            self._records[record.id] = record
        self._save()

    def query(self, vector: list[float], top_k: int = 5) -> list[VectorMatch]:
        if not self._records:
            return []

        query_vec = np.array(vector)
        query_norm = np.linalg.norm(query_vec)
        if query_norm == 0:
            return []

        scored: list[tuple[float, VectorRecord]] = []
        for record in self._records.values():
            rec_vec = np.array(record.vector)
            rec_norm = np.linalg.norm(rec_vec)
            if rec_norm == 0:
                continue
            similarity = float(np.dot(query_vec, rec_vec) / (query_norm * rec_norm))
            scored.append((similarity, record))

        scored.sort(key=lambda pair: pair[0], reverse=True)

        return [
            VectorMatch(id=record.id, score=score, text=record.text, metadata=record.metadata)
            for score, record in scored[:top_k]
        ]

    def count(self) -> int:
        return len(self._records)
