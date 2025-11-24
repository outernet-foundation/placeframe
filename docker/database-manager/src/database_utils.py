from __future__ import annotations

from contextlib import contextmanager

from psycopg import connect


@contextmanager
def postgres_cursor(database_name: str, host: str, user: str, password: str):
    with connect(
        host=host, port=5432, dbname=database_name, user=user, password=password, connect_timeout=5
    ) as connection:
        connection.autocommit = True
        with connection.cursor() as cursor:
            yield cursor
