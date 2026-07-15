import time

from utils.cache import InMemoryCache, cached


def test_in_memory_cache_get_set():
    cache = InMemoryCache()
    cache.set("key", {"a": 1})
    assert cache.get("key") == {"a": 1}


def test_in_memory_cache_missing_key_returns_none():
    cache = InMemoryCache()
    assert cache.get("nope") is None


def test_in_memory_cache_expires_after_ttl():
    cache = InMemoryCache()
    cache.set("key", "value", ttl_seconds=0.05)
    assert cache.get("key") == "value"
    time.sleep(0.1)
    assert cache.get("key") is None


def test_in_memory_cache_no_ttl_never_expires():
    cache = InMemoryCache()
    cache.set("key", "value")
    time.sleep(0.05)
    assert cache.get("key") == "value"


def test_in_memory_cache_delete():
    cache = InMemoryCache()
    cache.set("key", "value")
    cache.delete("key")
    assert cache.get("key") is None


def test_cached_decorator_only_calls_function_once_per_key(monkeypatch):
    from utils import cache as cache_module

    monkeypatch.setattr(cache_module, "_cache_instance", InMemoryCache())

    call_count = {"n": 0}

    @cached()
    def expensive(x):
        call_count["n"] += 1
        return x * 2

    assert expensive(5) == 10
    assert expensive(5) == 10
    assert call_count["n"] == 1


def test_cached_decorator_distinguishes_different_arguments(monkeypatch):
    from utils import cache as cache_module

    monkeypatch.setattr(cache_module, "_cache_instance", InMemoryCache())

    @cached()
    def expensive(x):
        return x * 2

    assert expensive(5) == 10
    assert expensive(6) == 12
