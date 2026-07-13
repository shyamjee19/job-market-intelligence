import json
import os

from config.constants import RAW_DATA_DIR, RAW_LATEST_FILENAME
from utils.exceptions import DataValidationError


def extract_latest_raw_jobs(source: str, raw_dir: str = RAW_DATA_DIR) -> list[dict]:
    """Reads the most recent raw snapshot the collector wrote for `source`."""
    latest_path = os.path.join(raw_dir, source, RAW_LATEST_FILENAME)

    if not os.path.exists(latest_path):
        raise DataValidationError(
            f"No raw data found at {latest_path} - run the collector for '{source}' first."
        )

    with open(latest_path, "r", encoding="utf-8") as file:
        return json.load(file)
