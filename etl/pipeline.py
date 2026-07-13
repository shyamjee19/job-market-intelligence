from collector.sources.registry import SOURCES
from etl.extract import extract_latest_raw_jobs
from etl.load import load_jobs, load_rejected
from etl.transform import transform_jobs
from etl.validate import validate_raw_record
from utils.logger import logger


def _run_for_source(source: str) -> dict:
    raw_jobs = extract_latest_raw_jobs(source)

    valid_raw: list[dict] = []
    rejected: list[tuple[dict, list[str]]] = []
    for raw in raw_jobs:
        errors = validate_raw_record(source, raw)
        (rejected.append((raw, errors)) if errors else valid_raw.append(raw))

    clean_jobs = transform_jobs(source, valid_raw)
    loaded = load_jobs(source, clean_jobs)
    rejected_count = load_rejected(source, rejected)

    stats = {
        "extracted": len(raw_jobs),
        "valid": len(valid_raw),
        "rejected": rejected_count,
        "loaded": loaded,
    }
    logger.info("[%s] ETL stats: %s", source, stats)
    return stats


def run_pipeline(source_name: str | None = None) -> dict[str, dict]:
    """Runs extract -> validate -> transform -> load for one source, or
    every registered source if none is given. A failure in one source is
    logged and skipped rather than aborting the others."""
    logger.info("ETL pipeline starting...")
    names = [source_name] if source_name else list(SOURCES)

    results: dict[str, dict] = {}
    for name in names:
        try:
            results[name] = _run_for_source(name)
        except Exception:
            logger.exception("[%s] ETL failed - skipping.", name)
            results[name] = {"error": True}

    logger.info("ETL pipeline finished: %s", results)
    return results


if __name__ == "__main__":
    run_pipeline()
