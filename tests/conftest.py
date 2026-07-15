import pytest

from config.settings import settings
from database.connection import ensure_database_exists, get_connection, init_schema
from utils.exceptions import DatabaseError

TEST_DB_NAME = f"{settings.DB_NAME}_test"


@pytest.fixture(scope="session")
def test_db():
    """Provisions an isolated `{DB_NAME}_test` database so integration
    tests never touch real data sitting in the configured dev database.
    Skips (rather than fails) if no Postgres server is reachable at all."""
    try:
        conn = get_connection(dbname="postgres")
        conn.close()
    except DatabaseError as e:
        pytest.skip(f"No database server available: {e}")

    ensure_database_exists(TEST_DB_NAME)
    init_schema(dbname=TEST_DB_NAME)

    return TEST_DB_NAME


@pytest.fixture
def use_test_db(test_db, monkeypatch):
    """For router/endpoint-level tests that go through FastAPI's
    TestClient rather than calling repository functions directly: those
    functions default to settings.DB_NAME when no dbname is passed, so
    redirecting that one setting for the test's duration routes every DB
    call made through the app - register, saved jobs, alerts, etc. -
    to the isolated test database instead of real dev data."""
    monkeypatch.setattr(settings, "DB_NAME", test_db)
    return test_db


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    """TestClient always reports the same synthetic client IP
    ("testclient"), so every router test in the suite shares one bucket
    per namespace - without this, tests that fire several requests
    (register/login flows especially) trip the real auth rate limiter
    and fail with 429s that have nothing to do with what they're testing."""
    from utils.rate_limiter import reset as reset_rate_limit

    for namespace in ("auth", "ai-chat", "api"):
        reset_rate_limit(namespace, "testclient")
    yield
