import sqlite3
from pathlib import Path
from .base import EventSink

class SqliteSink(EventSink):
    def __init__(self, database_path="eventlog.db"):
        self.database_path = Path(database_path)
        self._initialize_database()

    def _initialize_database(self):
        """Initialize the events table if it does not exist."""
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    event_type TEXT,
                    name TEXT,
                    suite TEXT,
                    status TEXT,
                    message TEXT
                )
            """)
            conn.commit()

    def handle_event(self, event_type, data):
        print(f"[SQLITE] Received event: {event_type} → {data.get('name')}")
        print(f"[DEBUG] Using SQLite DB: {self.database_path}")
        """Insert a single event into the database."""
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO events (timestamp, event_type, name, suite, status, message)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                data.get("timestamp"),
                data.get("event_type"),
                str(data.get("name")),
                str(data.get("suite")),
                data.get("status"),
                data.get("message")
            ))
            conn.commit()