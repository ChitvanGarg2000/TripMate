from Settings import settings
from psycopg.rows import dict_row
import psycopg

class PostgresConnect:
    def __init__(self):
        self.database_url = settings.PG_URL

    def get_database_url(self) -> str:
        if not self.database_url:
            raise ValueError("Database_url missing, please enter render external postgres url")

        database_url = self.database_url  # fix: was referencing bare name instead of self.database_url

        if "sslmode=" not in database_url:
            separator = '&' if '?' in database_url else '?'
            database_url += f"{separator}sslmode=require"

        return database_url

    def connect(self) -> psycopg.Connection:
        """
        Return an open psycopg Connection.

        Fix: the original used `with psycopg.connect(...) as conn: return conn`
        which closes the connection the moment the `with` block exits, so the
        returned object was already closed before the caller could use it.
        We now call psycopg.connect() without a context manager so the
        connection stays open and the caller (PostgresSaver) owns its lifetime.
        """
        database_url = self.get_database_url()
        return psycopg.connect(database_url, autocommit=True, row_factory=dict_row)
