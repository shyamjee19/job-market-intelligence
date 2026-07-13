"""Collector entrypoint: pulls job postings from the RemoteOK API and lands
an immutable, timestamped raw snapshot on disk.

This is the landing-zone layer of the pipeline - nothing here is
transformed, so the ETL stage can always replay a run from what's on disk.
"""
import json
import os
from datetime import datetime, timezone

from collector.api_client import APIClient
from config.constants import RAW_DATA_DIR, RAW_LATEST_FILENAME
from utils.logger import logger


def save_raw_snapshot(jobs: list[dict], raw_dir: str = RAW_DATA_DIR) -> str:
    os.makedirs(raw_dir, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    snapshot_path = os.path.join(raw_dir, f"jobs_{ts}.json")
    with open(snapshot_path, "w", encoding="utf-8") as file:
        json.dump(jobs, file, indent=2)

    # "latest" pointer so the ETL stage doesn't need to scan the directory.
    latest_path = os.path.join(raw_dir, RAW_LATEST_FILENAME)
    with open(latest_path, "w", encoding="utf-8") as file:
        json.dump(jobs, file, indent=2)

    logger.info("Raw snapshot saved to %s (%d records)", snapshot_path, len(jobs))
    return snapshot_path


def run() -> str:
    client = APIClient()
    jobs = client.get_jobs()

    if not jobs:
        logger.warning("No job records returned - nothing to save.")
        return ""

    return save_raw_snapshot(jobs)


if __name__ == "__main__":
    run()
