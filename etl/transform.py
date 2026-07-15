from config.constants import SOURCE_ADZUNA, SOURCE_ARBEITNOW, SOURCE_REMOTEOK, SOURCE_USAJOBS
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


def _normalize_adzuna(raw: dict) -> dict:
    """https://developer.adzuna.com/docs/search response shape. Adzuna has
    no explicit remote/onsite flag, so remote_type defaults to "onsite" and
    only gets refined by the shared hybrid-keyword scan."""
    position = clean_text(raw.get("title"))
    location = clean_text((raw.get("location") or {}).get("display_name"))
    description = clean_text(raw.get("description"))
    company = clean_text((raw.get("company") or {}).get("display_name"))
    category = (raw.get("category") or {}).get("label")
    salary_min, salary_max = normalize_salary(raw.get("salary_min"), raw.get("salary_max"))

    return {
        "source": SOURCE_ADZUNA,
        "external_id": str(raw["id"]),
        "company": company,
        "position": position,
        "location": location,
        "country": infer_country(location),
        "remote_type": detect_remote_type("onsite", position, description),
        "salary_min": salary_min,
        "salary_max": salary_max,
        "date_posted": parse_date(raw.get("created")),
        "tags": normalize_tags([category] if category else []),
        "job_url": clean_text(raw.get("redirect_url")),
        "apply_url": clean_text(raw.get("redirect_url")),
        "description": description,
    }


def _normalize_usajobs(raw: dict) -> dict:
    """https://developer.usajobs.gov/API-Reference/GET-api-Search response
    shape - everything meaningful sits under MatchedObjectDescriptor.
    USAJobs is US-only by definition, so country is hardcoded rather than
    left to the same free-text inference used for the other sources; a
    "Remote" mention in USAJobs' own location display is a real signal
    federal postings use, so it's checked before falling back to onsite."""
    descriptor = raw.get("MatchedObjectDescriptor") or {}
    position = clean_text(descriptor.get("PositionTitle"))
    location = clean_text(descriptor.get("PositionLocationDisplay"))
    description = clean_text((descriptor.get("UserArea") or {}).get("Details", {}).get("JobSummary"))
    company = clean_text(descriptor.get("OrganizationName"))
    remuneration = (descriptor.get("PositionRemuneration") or [{}])[0]
    salary_min, salary_max = normalize_salary(remuneration.get("MinimumRange"), remuneration.get("MaximumRange"))
    categories = descriptor.get("JobCategory") or []
    tags = normalize_tags([c.get("Name") for c in categories if c.get("Name")])
    base_remote_type = "remote" if location and "remote" in location.lower() else "onsite"

    return {
        "source": SOURCE_USAJOBS,
        "external_id": str(raw.get("MatchedObjectId") or descriptor.get("PositionID")),
        "company": company,
        "position": position,
        "location": location,
        "country": "United States",
        "remote_type": detect_remote_type(base_remote_type, position, description),
        "salary_min": salary_min,
        "salary_max": salary_max,
        "date_posted": parse_date(descriptor.get("PublicationStartDate")),
        "tags": tags,
        "job_url": clean_text(descriptor.get("PositionURI")),
        "apply_url": clean_text(descriptor.get("PositionURI")),
        "description": description,
    }


NORMALIZERS = {
    SOURCE_REMOTEOK: _normalize_remoteok,
    SOURCE_ARBEITNOW: _normalize_arbeitnow,
    SOURCE_ADZUNA: _normalize_adzuna,
    SOURCE_USAJOBS: _normalize_usajobs,
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
