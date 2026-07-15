"""Builds/refreshes the RAG vector store from the current jobs table. Run
it after the ETL pipeline loads new data - it's a separate, explicit step
rather than automatic, so re-embedding (and its API cost) only happens
when asked for:

    python -m ai.services.rag_indexer
"""
import re

from ai.providers.registry import get_embedding_provider
from ai.vectorstore.base import VectorRecord
from ai.vectorstore.registry import get_vector_store
from database.queries import list_all_jobs_for_indexing
from utils.logger import logger

_BATCH_SIZE = 100  # keep each embeddings API call reasonably sized
_DESCRIPTION_CHAR_LIMIT = 2000  # full HTML descriptions can be huge; keep each embedded chunk small


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text or "")


def job_to_text(job: dict) -> str:
    """The text actually embedded and later shown to the LLM as context -
    deliberately compact and structured, not the raw HTML description."""
    salary = ""
    if job.get("salary_min") or job.get("salary_max"):
        salary = f"Salary: ${job.get('salary_min') or '?'}-${job.get('salary_max') or '?'}. "

    tags = ", ".join(job.get("tags") or [])
    description = _strip_html(job.get("description") or "")[:_DESCRIPTION_CHAR_LIMIT]

    return (
        f"Position: {job.get('position')} at {job.get('company')}. "
        f"Location: {job.get('location') or 'not specified'} ({job.get('remote_type') or 'unknown'}). "
        f"{salary}"
        f"Skills/tags: {tags}. "
        f"Source: {job.get('source')}. "
        f"Description: {description}"
    )


def run_indexer() -> int:
    jobs = list_all_jobs_for_indexing()
    if not jobs:
        logger.warning("No jobs to index.")
        return 0

    embedder = get_embedding_provider()
    store = get_vector_store(dimensions=embedder.dimensions)

    indexed = 0
    for start in range(0, len(jobs), _BATCH_SIZE):
        batch = jobs[start : start + _BATCH_SIZE]
        texts = [job_to_text(job) for job in batch]
        vectors = embedder.embed(texts)

        records = [
            VectorRecord(
                id=str(job["id"]),
                vector=vector,
                text=text,
                metadata={
                    "job_id": str(job["id"]),
                    "company": job.get("company"),
                    "position": job.get("position"),
                    "source": job.get("source"),
                },
            )
            for job, text, vector in zip(batch, texts, vectors)
        ]
        store.upsert(records)
        indexed += len(records)
        logger.info("Indexed %d/%d jobs", indexed, len(jobs))

    logger.info("RAG indexing complete: %d jobs embedded into '%s' vector store.", indexed, store.name)
    return indexed


if __name__ == "__main__":
    run_indexer()
