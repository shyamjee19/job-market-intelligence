from collector.sources.adzuna import AdzunaSource
from collector.sources.arbeitnow import ArbeitnowSource
from collector.sources.base import JobSource
from collector.sources.remoteok import RemoteOKSource
from collector.sources.usajobs import USAJobsSource
from config.settings import settings

# Sources that need no credentials are always active. Sources that need an
# API key/account list the settings.py attributes required to activate -
# they're only added to SOURCES once every one of those is set, so an
# unconfigured .env doesn't produce constant fetch failures on every run.
_ALWAYS_ON: list[type[JobSource]] = [RemoteOKSource, ArbeitnowSource]

_REQUIRES_CONFIG: dict[type[JobSource], list[str]] = {
    AdzunaSource: ["ADZUNA_APP_ID", "ADZUNA_APP_KEY"],
    USAJobsSource: ["USAJOBS_API_KEY", "USAJOBS_EMAIL"],
}

_ALL_CLASSES_BY_NAME: dict[str, type[JobSource]] = {
    cls.name: cls for cls in [*_ALWAYS_ON, *_REQUIRES_CONFIG]
}


def _is_configured(cls: type[JobSource]) -> bool:
    required = _REQUIRES_CONFIG.get(cls, [])
    return all(getattr(settings, key, None) for key in required)


SOURCES: dict[str, JobSource] = {
    cls.name: cls()
    for cls in [*_ALWAYS_ON, *_REQUIRES_CONFIG]
    if _is_configured(cls)
}


def get_source(name: str) -> JobSource:
    if name in SOURCES:
        return SOURCES[name]

    cls = _ALL_CLASSES_BY_NAME.get(name)
    if cls is not None:
        missing = _REQUIRES_CONFIG.get(cls, [])
        raise ValueError(f"Source '{name}' is registered but not configured - set {', '.join(missing)} in .env")

    raise ValueError(f"Unknown source '{name}'. Available: {sorted(_ALL_CLASSES_BY_NAME)}")
