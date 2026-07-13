from collector.sources.arbeitnow import ArbeitnowSource
from collector.sources.base import JobSource
from collector.sources.remoteok import RemoteOKSource

# Add a new source: implement JobSource in this package, add one line here.
SOURCES: dict[str, JobSource] = {
    source.name: source for source in (RemoteOKSource(), ArbeitnowSource())
}


def get_source(name: str) -> JobSource:
    try:
        return SOURCES[name]
    except KeyError:
        raise ValueError(f"Unknown source '{name}'. Available: {sorted(SOURCES)}") from None
