import requests

from collector.retry import retry
from config.settings import settings
from utils.exceptions import APIRequestError
from utils.logger import logger


class APIClient:
    def __init__(self):
        self.url = settings.REMOTEOK_API_URL
        self.headers = {"User-Agent": "JobPulse/1.0"}

    @retry(max_attempts=settings.API_RETRY_ATTEMPTS, delay=settings.API_RETRY_DELAY_SECONDS)
    def get_jobs(self) -> list[dict]:
        logger.info("Calling RemoteOK API at %s", self.url)

        response = requests.get(self.url, headers=self.headers, timeout=settings.API_TIMEOUT_SECONDS)
        response.raise_for_status()

        payload = response.json()
        if not isinstance(payload, list) or len(payload) < 1:
            raise APIRequestError(f"Unexpected API response shape: {type(payload)}")

        logger.info("API call successful - %d records received", len(payload))

        # RemoteOK's first record is feed metadata (no "id" field), not a job.
        return payload[1:] if len(payload) > 1 else []