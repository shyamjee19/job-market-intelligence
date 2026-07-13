from database.connection import get_connection


def test_database_connection(test_db):
    conn = get_connection(dbname=test_db)
    try:
        assert conn.closed == 0
    finally:
        conn.close()
