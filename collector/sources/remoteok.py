from collector.api_client import APIClient
from collector.sources.base import JobSource
from config.constants import SOURCE_REMOTEOK


class RemoteOKSource(JobSource):
    name = SOURCE_REMOTEOK

    def __init__(self):
        self._client = APIClient()

    def fetch(self) -> list[dict]:
        return self._client.get_jobs()
