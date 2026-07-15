import requests

from collector.retry import retry
from collector.sources.base import JobSource
from config.constants import SOURCE_ADZUNA
from config.settings import settings
from utils.exceptions import APIRequestError
from utils.logger import logger


class AdzunaSource(JobSource):
    """https://developer.adzuna.com/docs/search - one page of the most
    recent results for the configured country (ADZUNA_COUNTRY, default
    "us"). Adzuna is multi-country, but one JobSource = one API account
    the way this pipeline is structured; add another instance/registry
    entry per country if you need more than one."""

    name = SOURCE_ADZUNA

    def __init__(self):
        self.url = f"{settings.ADZUNA_API_URL}/{settings.ADZUNA_COUNTRY}/search/1"

    @retry(max_attempts=settings.API_RETRY_ATTEMPTS, delay=settings.API_RETRY_DELAY_SECONDS)
    def fetch(self) -> list[dict]:
        logger.info("Calling Adzuna API at %s", self.url)

        response = requests.get(
            self.url,
            params={
                "app_id": settings.ADZUNA_APP_ID,
                "app_key": settings.ADZUNA_APP_KEY,
                "results_per_page": 50,
                "content-type": "application/json",
            },
            timeout=settings.API_TIMEOUT_SECONDS,
        )
        response.raise_for_status()

        payload = response.json()
        jobs = payload.get("results") if isinstance(payload, dict) else None
        if not isinstance(jobs, list):
            raise APIRequestError(f"Unexpected Adzuna response shape: {type(payload)}")

        logger.info("Adzuna call successful - %d records received", len(jobs))
        return jobs
