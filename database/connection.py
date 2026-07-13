from contextlib import contextmanager

import psycopg2

from config.settings import settings
from utils.exceptions import DatabaseError
from utils.logger import logger


def get_connection(dbname: str | None = None):
    try:
        return psycopg2.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=dbname or settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
        )
    except psycopg2.OperationalError as e:
        raise DatabaseError(f"Could not connect to database: {e}") from e


@contextmanager
def get_db_cursor(commit: bool = False, dbname: str | None = None, cursor_factory=None):
    """Context manager that yields a cursor and always closes the
    connection, committing only if the caller asks for it and no error
    was raised."""
    conn = get_connection(dbname=dbname)
    try:
        cursor = conn.cursor(cursor_factory=cursor_factory)
        try:
            yield cursor
            if commit:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
    finally:
        conn.close()


def init_schema(schema_path: str = "database/schema.sql", dbname: str | None = None) -> None:
    with open(schema_path, "r", encoding="utf-8") as file:
        schema_sql = file.read()

    with get_db_cursor(commit=True, dbname=dbname) as cursor:
        cursor.execute(schema_sql)

    logger.info("Database schema is up to date%s.", f" ({dbname})" if dbname else "")


def ensure_database_exists(dbname: str) -> None:
    """Creates `dbname` if it doesn't exist yet, connecting to the default
    'postgres' maintenance database to issue the CREATE DATABASE. Used to
    provision an isolated test database on demand."""
    conn = get_connection(dbname="postgres")
    conn.autocommit = True
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
            if cursor.fetchone() is None:
                cursor.execute(f'CREATE DATABASE "{dbname}"')
                logger.info("Created database %s", dbname)
    finally:
        conn.close()
