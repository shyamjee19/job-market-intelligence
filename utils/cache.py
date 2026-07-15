"""Generic cache: Redis-backed when REDIS_URL is set and reachable,
otherwise an in-memory dict with the same TTL semantics - same
"degrade gracefully, don't crash" pattern as every other optional
integration in this project (Adzuna, Pinecone, ...).

`cached()` is the decorator most call sites actually want - see
api/routes/stats.py for how it wraps an endpoint function.
"""
import functools
import time
from abc import ABC, abstractmethod

from config.settings import settings
from utils.logger import logger


class Cache(ABC):
    @abstractmethod
    def get(self, key: str):
        raise NotImplementedError

    @abstractmethod
    def set(self, key: str, value, ttl_seconds: int | None = None) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, key: str) -> None:
        raise NotImplementedError


class InMemoryCache(Cache):
    name = "memory"

    def __init__(self):
        self._store: dict[str, tuple[object, float | None]] = {}

    def get(self, key: str):
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if expires_at is not None and expires_at < time.time():
            del self._store[key]
            return None
        return value

    def set(self, key: str, value, ttl_seconds: int | None = None) -> None:
        expires_at = time.time() + ttl_seconds if ttl_seconds else None
        self._store[key] = (value, expires_at)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)


class RedisCache(Cache):
    name = "redis"

    def __init__(self):
        import redis

        self._client = redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=3)
        self._client.ping()  # fail fast here, not on the first real request

    def get(self, key: str):
        import json

        raw = self._client.get(key)
        return json.loads(raw) if raw is not None else None

    def set(self, key: str, value, ttl_seconds: int | None = None) -> None:
        import json

        # Postgres rows can carry Decimal/date/datetime values that plain
        # json.dumps can't handle - default=str stringifies them instead
        # of raising. FastAPI's response_model then coerces those strings
        # back to the right type on the way out (Pydantic parses "2026-
        # 07-15" back to a date, "55000.0" back to a float, etc.), so a
        # Redis cache hit round-trips correctly despite the detour through
        # a string. InMemoryCache never serializes, so it isn't affected.
        self._client.set(key, json.dumps(value, default=str), ex=ttl_seconds)

    def delete(self, key: str) -> None:
        self._client.delete(key)


_cache_instance: Cache | None = None


def get_cache() -> Cache:
    global _cache_instance
    if _cache_instance is not None:
        return _cache_instance

    if settings.REDIS_URL:
        try:
            _cache_instance = RedisCache()
            logger.info("Cache backend: Redis")
        except Exception:
            logger.warning("REDIS_URL is set but unreachable - falling back to in-memory cache.", exc_info=True)
            _cache_instance = InMemoryCache()
    else:
        _cache_instance = InMemoryCache()

    return _cache_instance


def reset_cache() -> None:
    """Test helper - forces get_cache() to re-evaluate REDIS_URL on next call."""
    global _cache_instance
    _cache_instance = None


def cached(ttl_seconds: int | None = None):
    """Caches a function's return value, keyed on its qualified name and
    arguments. Only use on functions whose return value is JSON-
    serializable (dicts/lists of primitives) - exactly what the stats
    endpoints already return."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache()
            key = f"{func.__module__}.{func.__qualname__}:{args}:{sorted(kwargs.items())}"

            hit = cache.get(key)
            if hit is not None:
                return hit

            result = func(*args, **kwargs)
            cache.set(key, result, ttl_seconds or settings.CACHE_DEFAULT_TTL_SECONDS)
            return result

        return wrapper

    return decorator
