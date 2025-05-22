# backend/sqlite_reader.py
import sqlite3
from .event_reader import EventReader
from helpers.config_loader import load_config
from helpers.sql_definitions import SELECT_ALL_EVENTS, DELETE_ALL_EVENTS

class SqliteEventReader(EventReader):
    def __init__(self, database_path = None, conn = None):
        config = load_config()
        self.database_path = (
            database_path
            or config.get("sqlite_path", "eventlog.db")
        )
        self.conn = conn 

    def _get_connection(self):
        if self.conn is not None:
            return self.conn, False  # False = do not close the connection
        else:
            return sqlite3.connect(self.database_path), True #True = close the connection

    def get_events(self):
        print("DEBUG: Executing SQL ->", SELECT_ALL_EVENTS)
        conn, should_close = self._get_connection()
        cursor = conn.cursor()
        rows = cursor.execute(SELECT_ALL_EVENTS).fetchall()
        columns = [col[0] for col in cursor.description]
        events = [dict(zip(columns, row)) for row in rows]
        if should_close:
            conn.close()
        return events

    def clear_events(self):
        conn, should_close = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(DELETE_ALL_EVENTS)
        conn.commit()
        if should_close:
            conn.close()
