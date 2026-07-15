import pytest

from collector.sources.registry import SOURCES, get_source
from config.settings import settings


def test_no_key_sources_are_always_active():
    assert "remoteok" in SOURCES
    assert "arbeitnow" in SOURCES


def test_adzuna_activation_matches_its_configuration():
    # Asserts the invariant (active iff configured) instead of hardcoding
    # today's .env state, so this doesn't break the moment credentials
    # are added or removed in a given environment.
    is_configured = bool(settings.ADZUNA_APP_ID and settings.ADZUNA_APP_KEY)
    assert ("adzuna" in SOURCES) == is_configured


def test_usajobs_activation_matches_its_configuration():
    is_configured = bool(settings.USAJOBS_API_KEY and settings.USAJOBS_EMAIL)
    assert ("usajobs" in SOURCES) == is_configured


def test_get_source_on_unconfigured_source_explains_whats_missing():
    if "adzuna" in SOURCES:
        pytest.skip("Adzuna is configured in this environment")
    with pytest.raises(ValueError, match="ADZUNA_APP_ID"):
        get_source("adzuna")


def test_get_source_on_truly_unknown_name_raises():
    with pytest.raises(ValueError, match="Unknown source"):
        get_source("not-a-real-source")


def test_get_source_on_active_source_returns_it():
    assert get_source("remoteok").name == "remoteok"
