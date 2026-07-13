from abc import ABC, abstractmethod


class JobSource(ABC):
    """A pluggable job-postings source.

    Implementations only need to return raw records exactly as their API
    responds - normalization into the common schema happens later, in
    etl/transform.py, dispatched off `name`. To add a new source (Adzuna,
    Jooble, USAJobs, Kaggle, ...): add its URL/key to config/settings.py,
    implement fetch() here, register it in collector/sources/registry.py,
    and add a matching normalizer in etl/transform.py. Nothing else in the
    pipeline (validate/load/API/frontend) needs to change.
    """

    name: str

    @abstractmethod
    def fetch(self) -> list[dict]:
        raise NotImplementedError
