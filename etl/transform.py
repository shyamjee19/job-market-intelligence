from utils.helper import clean_text, dedupe_by_key, normalize_salary, normalize_tags, parse_date
from utils.logger import logger


def _transform_one(raw: dict) -> dict | None:
    job_id = raw.get("id")
    company = clean_text(raw.get("company"))
    position = clean_text(raw.get("position"))

    # A job posting is only useful downstream if we can identify it and
    # know who's hiring for what - everything else can be missing.
    if not job_id or not company or not position:
        return None

    salary_min, salary_max = normalize_salary(raw.get("salary_min"), raw.get("salary_max"))

    return {
        "job_id": int(job_id),
        "company": company,
        "position": position,
        "location": clean_text(raw.get("location")),
        "salary_min": salary_min,
        "salary_max": salary_max,
        "date_posted": parse_date(raw.get("date")),
        "tags": normalize_tags(raw.get("tags")),
        "job_url": clean_text(raw.get("url")),
        "apply_url": clean_text(raw.get("apply_url")),
        "description": clean_text(raw.get("description")),
    }


def transform_jobs(raw_jobs: list[dict]) -> list[dict]:
    """Cleans, validates, and deduplicates raw job records. Records missing
    a required field are dropped rather than raising - one bad posting
    shouldn't fail the whole batch."""
    transformed = []
    rejected = 0

    for raw in raw_jobs:
        try:
            clean = _transform_one(raw)
        except (TypeError, ValueError):
            clean = None

        if clean is None:
            rejected += 1
        else:
            transformed.append(clean)

    deduped = dedupe_by_key(transformed, "job_id")

    logger.info(
        "Transformed %d/%d records (%d rejected, %d duplicate job_ids removed)",
        len(deduped), len(raw_jobs), rejected, len(transformed) - len(deduped),
    )

    return deduped
