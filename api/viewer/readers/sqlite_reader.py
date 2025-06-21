# backend/sqlite_reader.py
import sqlite3
from .reader import Reader
from shared.helpers.config_loader import load_config
from shared.helpers.sql_definitions import (
    SELECT_ALL_EVENTS,
    DELETE_ALL_EVENTS,
    SELECT_ALL_APP_LOGS
)
from typing import List, Dict

class SqliteReader(Reader):
    def __init__(self, database_path=None, conn=None):
        super().__init__()
        config = load_config()
        self.database_path = database_path or config.get("sqlite_path", "eventlog.db")
        self.conn = conn

    def _get_connection(self):
        self.logger.debug("Connecting to database at %s", self.database_path)
        if self.conn is not None:
            return self.conn, False  # False = do not close the connection
        else:
            return sqlite3.connect(self.database_path), True  # True = close the connection

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
        return self._fetch_all_as_dicts(SELECT_ALL_EVENTS)

    def _get_app_logs(self) -> List[Dict]:
        return self._fetch_all_as_dicts(SELECT_ALL_APP_LOGS)

    def _clear_events(self) -> None:
        conn, should_close = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(DELETE_ALL_EVENTS)
            conn.commit()
        finally:
            if should_close:
                conn.close()