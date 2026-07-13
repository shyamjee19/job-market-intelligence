from config.constants import SOURCE_ARBEITNOW, SOURCE_REMOTEOK
from utils.geo import infer_country
from utils.helper import (
    clean_text,
    dedupe_by_key,
    detect_remote_type,
    normalize_salary,
    normalize_tags,
    parse_date,
    parse_epoch_date,
)
from utils.logger import logger


def _normalize_remoteok(raw: dict) -> dict:
    salary_min, salary_max = normalize_salary(raw.get("salary_min"), raw.get("salary_max"))
    position = clean_text(raw.get("position"))
    location = clean_text(raw.get("location"))
    description = clean_text(raw.get("description"))

    return {
        "source": SOURCE_REMOTEOK,
        "external_id": str(raw["id"]),
        "company": clean_text(raw.get("company")),
        "position": position,
        "location": location,
        "country": infer_country(location),
        "remote_type": detect_remote_type("remote", position, description),
        "salary_min": salary_min,
        "salary_max": salary_max,
        "date_posted": parse_date(raw.get("date")),
        "tags": normalize_tags(raw.get("tags")),
        "job_url": clean_text(raw.get("url")),
        "apply_url": clean_text(raw.get("apply_url")),
        "description": description,
    }


def _normalize_arbeitnow(raw: dict) -> dict:
    tags = list(raw.get("tags") or []) + list(raw.get("job_types") or [])
    position = clean_text(raw.get("title"))
    location = clean_text(raw.get("location"))
    description = clean_text(raw.get("description"))
    base_remote_type = "remote" if raw.get("remote") else "onsite"

    return {
        "source": SOURCE_ARBEITNOW,
        "external_id": str(raw["slug"]),
        "company": clean_text(raw.get("company_name")),
        "position": position,
        "location": location,
        "country": infer_country(location),
        "remote_type": detect_remote_type(base_remote_type, position, description),
        "salary_min": None,
        "salary_max": None,
        "date_posted": parse_epoch_date(raw.get("created_at")),
        "tags": normalize_tags(tags),
        "job_url": clean_text(raw.get("url")),
        "apply_url": clean_text(raw.get("url")),
        "description": description,
    }


NORMALIZERS = {
    SOURCE_REMOTEOK: _normalize_remoteok,
    SOURCE_ARBEITNOW: _normalize_arbeitnow,
}


def transform_jobs(source: str, raw_jobs: list[dict]) -> list[dict]:
    """Normalizes already-validated raw records from one source into the
    common schema, then deduplicates by external_id (later record in the
    batch wins)."""
    normalizer = NORMALIZERS[source]
    normalized = [normalizer(raw) for raw in raw_jobs]
    deduped = dedupe_by_key(normalized, "external_id")

    if len(deduped) != len(normalized):
        logger.info(
            "[%s] Removed %d duplicate external_id(s) within batch.",
            source, len(normalized) - len(deduped),
        )

    return deduped
