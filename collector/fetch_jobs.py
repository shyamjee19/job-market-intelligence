"""Collector entrypoint: pulls job postings from every registered source
and lands an immutable, timestamped raw snapshot per source on disk
(data/raw/<source>/jobs_*.json) - the Bronze layer. Nothing here is
transformed, so the ETL stage can always replay a run from what's on disk.
"""
import json
import os
from datetime import datetime, timezone

from collector.sources.registry import SOURCES, get_source
from config.constants import RAW_DATA_DIR, RAW_LATEST_FILENAME
from utils.logger import logger


def save_raw_snapshot(source_name: str, jobs: list[dict], raw_dir: str = RAW_DATA_DIR) -> str:
    source_dir = os.path.join(raw_dir, source_name)
    os.makedirs(source_dir, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    snapshot_path = os.path.join(source_dir, f"jobs_{ts}.json")
    with open(snapshot_path, "w", encoding="utf-8") as file:
        json.dump(jobs, file, indent=2)

    # "latest" pointer so the ETL stage doesn't need to scan the directory.
    latest_path = os.path.join(source_dir, RAW_LATEST_FILENAME)
    with open(latest_path, "w", encoding="utf-8") as file:
        json.dump(jobs, file, indent=2)

    logger.info("[%s] Raw snapshot saved to %s (%d records)", source_name, snapshot_path, len(jobs))
    return snapshot_path


def collect_source(source_name: str) -> str:
    source = get_source(source_name)
    jobs = source.fetch()

    if not jobs:
        logger.warning("[%s] No job records returned - nothing to save.", source_name)
        return ""

    return save_raw_snapshot(source_name, jobs)


def run(source_name: str | None = None) -> dict[str, str]:
    """Collects one source, or all registered sources if none is given.
    A failure in one source doesn't stop the others - it's logged and
    skipped so a flaky third-party API can't block the whole run."""
    names = [source_name] if source_name else list(SOURCES)
    results: dict[str, str] = {}

    for name in names:
        try:
            results[name] = collect_source(name)
        except Exception:
            logger.exception("[%s] Collection failed - skipping.", name)
            results[name] = ""

    return results


if __name__ == "__main__":
    run()
