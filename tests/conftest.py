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
