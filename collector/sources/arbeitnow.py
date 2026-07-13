import requests

from collector.retry import retry
from collector.sources.base import JobSource
from config.constants import SOURCE_ARBEITNOW
from config.settings import settings
from utils.exceptions import APIRequestError
from utils.logger import logger


class ArbeitnowSource(JobSource):
    name = SOURCE_ARBEITNOW

    def __init__(self):
        self.url = settings.ARBEITNOW_API_URL

    @retry(max_attempts=settings.API_RETRY_ATTEMPTS, delay=settings.API_RETRY_DELAY_SECONDS)
    def fetch(self) -> list[dict]:
        logger.info("Calling Arbeitnow API at %s", self.url)

        response = requests.get(self.url, timeout=settings.API_TIMEOUT_SECONDS)
        response.raise_for_status()

        payload = response.json()
        jobs = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(jobs, list):
            raise APIRequestError(f"Unexpected Arbeitnow response shape: {type(payload)}")

        logger.info("Arbeitnow call successful - %d records received", len(jobs))
        return jobs
