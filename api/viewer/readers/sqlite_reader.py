# backend/sqlite_reader.py
import sqlite3
from .reader import Reader
from shared.helpers.config_loader import load_config
import shared.helpers.sql_definitions as sql_definitions

from typing import List, Dict

class SqliteReader(Reader):
    def __init__(self, database_url=None, conn=None):
        super().__init__()
        config = load_config()
        raw_path = database_url or config.get("database_url", "sqlite:///eventlog.db")

        # Strip 'sqlite:///' prefix if present
        if raw_path.startswith("sqlite:///"):
            self.database_url = raw_path.replace("sqlite:///", "", 1)
        else:
            self.database_url = raw_path

        self.conn = conn

    def _get_connection(self):
        self.logger.debug("Connecting to Sqlite at %s", self.database_url)
        if self.conn is not None:
            return self.conn, False  # False = do not close the connection
        else:
            return sqlite3.connect(self.database_url), True  # True = close the connection

    def _fetch_all_as_dicts(self, query: str) -> List[Dict]:
        self.logger.debug("Executing SQL -> %s", query)
        conn, should_close = self._get_connection()
        try:
            cursor = conn.cursor()
            rows = cursor.execute(query).fetchall()
            columns = [col[0] for col in cursor.description]
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
            cursor = conn.cursor()
            cursor.execute(sql_definitions.DELETE_ALL_EVENTS)
            conn.commit()
        finally:
            if should_close:
                conn.close()