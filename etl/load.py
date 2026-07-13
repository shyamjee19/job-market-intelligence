from database.repository import insert_rejected, upsert_jobs


def load_jobs(source: str, clean_jobs: list[dict]) -> int:
    return upsert_jobs(source, clean_jobs)


def load_rejected(source: str, rejected: list[tuple[dict, list[str]]]) -> int:
    return insert_rejected(source, rejected)
