import requests

from collector.retry import retry
from collector.sources.base import JobSource
from config.constants import SOURCE_USAJOBS
from config.settings import settings
from utils.exceptions import APIRequestError
from utils.logger import logger


class USAJobsSource(JobSource):
    """https://developer.usajobs.gov/API-Reference/GET-api-Search - US
    federal government postings. Requires an API key plus a contact email
    sent as the User-Agent header (USAJobs' own API terms, not optional)."""

    name = SOURCE_USAJOBS

    def __init__(self):
        self.url = settings.USAJOBS_API_URL

    @retry(max_attempts=settings.API_RETRY_ATTEMPTS, delay=settings.API_RETRY_DELAY_SECONDS)
    def fetch(self) -> list[dict]:
        logger.info("Calling USAJobs API at %s", self.url)

        response = requests.get(
            self.url,
            headers={
                "Host": "data.usajobs.gov",
                "User-Agent": settings.USAJOBS_EMAIL,
                "Authorization-Key": settings.USAJOBS_API_KEY,
            },
            params={"ResultsPerPage": 250},
            timeout=settings.API_TIMEOUT_SECONDS,
        )
        response.raise_for_status()

        payload = response.json()
        items = (
            payload.get("SearchResult", {}).get("SearchResultItems")
            if isinstance(payload, dict) else None
        )
        if not isinstance(items, list):
            raise APIRequestError(f"Unexpected USAJobs response shape: {type(payload)}")

        logger.info("USAJobs call successful - %d records received", len(items))
        return items
