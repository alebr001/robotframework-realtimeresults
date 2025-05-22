# backend/sqlite_reader.py
import sqlite3
from .event_reader import EventReader
from helpers.config_loader import load_config

class SqliteEventReader(EventReader):
    def __init__(self, database_path="eventlog.db"):
        self.database_path = database_path

    def get_events(self):
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            rows = cursor.execute("""
                SELECT timestamp, event_type, name, suite, status, message
                FROM events
                ORDER BY timestamp ASC
                LIMIT 100
            """).fetchall()
            return [dict(zip(["timestamp", "event_type", "name", "suite", "status", "message"], row)) for row in rows]
        
    def clear_events(self):
        config = load_config()
        with sqlite3.connect(config.get("sqlite_path", "eventlog.db")) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM events")
            conn.commit()