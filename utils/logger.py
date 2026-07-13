import logging
import os

from config.constants import LOG_DIR, LOG_FILENAME
from config.settings import settings


def _build_logger() -> logging.Logger:
    os.makedirs(LOG_DIR, exist_ok=True)

    log = logging.getLogger("job_market_intelligence")
    log.setLevel(settings.LOG_LEVEL)

    if log.handlers:
        # Reuse the existing setup instead of stacking duplicate handlers
        # when this module is imported multiple times.
        return log

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    log.addHandler(console_handler)

    file_handler = logging.FileHandler(
        os.path.join(LOG_DIR, LOG_FILENAME), encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    log.addHandler(file_handler)

    return log


logger = _build_logger()
