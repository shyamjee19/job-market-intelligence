from database.repository import upsert_jobs


def load_jobs(clean_jobs: list[dict]) -> int:
    return upsert_jobs(clean_jobs)
