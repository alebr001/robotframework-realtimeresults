# api/viewer/readers/postgres_reader.py

import psycopg2
from .reader import Reader
from shared.helpers.config_loader import load_config
import shared.helpers.sql_definitions as sql_definitions

from typing import List, Dict

class PostgresReader(Reader):
    def __init__(self, database_url=None, conn=None):
        super().__init__()
        config = load_config()
        self.database_url = database_url or config.get("database_url")
        self.conn = conn

    def _get_connection(self):
        self.logger.debug("Connecting to PostgreSQL at %s", self.database_url)
        if self.conn is not None:
            return self.conn, False
        else:
            try:
                return psycopg2.connect(self.database_url), True
            except psycopg2.OperationalError as e:
                self.logger.error("Failed to connect to PostgreSQL is the service running? %s", e)
                raise

    def _fetch_all_as_dicts(self, query: str) -> List[Dict]:
        self.logger.debug("Executing SQL -> %s", query)
        conn, should_close = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
        finally:
            if should_close:
                conn.close()

    def _get_events(self) -> List[Dict]:
        return self._fetch_all_as_dicts(sql_definitions.SELECT_ALL_EVENTS)

    def _get_app_logs(self) -> List[Dict]:
        return self._fetch_all_as_dicts(sql_definitions.SELECT_ALL_APP_LOGS)

    def _clear_events(self) -> None:
        conn, should_close = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql_definitions.DELETE_ALL_EVENTS)
                conn.commit()
        finally:
            if should_close:
                conn.close()
