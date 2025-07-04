import sqlite3
from pathlib import Path

from shared.helpers.ensure_db_schema import ensure_schema
from .base import EventSink
from shared.helpers.sql_definitions import (
    INSERT_EVENT,
    INSERT_RF_LOG_MESSAGE
)

# SqliteSink (sync variant): intended for Robot Framework listener events only.
# Supports only test/suite events and RF log messages.
# For app_logs and metrics, use AsyncSqliteSink instead.

class SqliteSink(EventSink):
    def __init__(self, database_path="eventlog.db"):
        super().__init__()
        self.database_path = Path(database_path)
        self.dispatch_map = {
            "start_test": self._insert_event,
            "end_test": self._insert_event,
            "start_suite": self._insert_event,
            "start_keyword": self._insert_event,
            "end_keyword": self._insert_event,
            "end_suite": self._insert_event,
            "log_message": self._insert_rf_log
        }
        self._initialize_database()

    def _initialize_database(self):
        self.logger.info("Ensuring tables in %s exist", self.database_path)
        try:
            ensure_schema(self.database_path)
        except Exception as e:
            self.logger.warning("[SQLITE_SYNC] DB init failed: %s", e)
            raise

    def _handle_event(self, data):
        event_type = data.get("event_type")
        handler = self.dispatch_map.get(event_type)
        if handler:
            try:
                with sqlite3.connect(self.database_path) as conn:
                    handler(conn, data)
                    conn.commit()
            except Exception as e:
                self.logger.warning("[SQLITE_SYNC] Failed to process event_type '%s': %s", event_type, e)
                raise
        else:
            self.logger.warning("[SQLITE_SYNC] No handler for event_type: %s", event_type)

    def _insert_event(self, conn, data):
        tags = data.get("tags", [])
        tag_string = ",".join(str(tag) for tag in (tags if isinstance(tags, list) else [str(tags)]))
        conn.execute(INSERT_EVENT, (
            data.get("testid"),
            data.get("timestamp"),
            data.get("event_type"),
            str(data.get("name")),
            str(data.get("suite")),
            data.get("status"),
            data.get("message"),
            data.get("elapsed"),
            tag_string
        ))

    def _insert_rf_log(self, conn, data):
        conn.execute(INSERT_RF_LOG_MESSAGE, (
            data.get("testid"),
            data.get("timestamp"),
            data.get("message"),
            data.get("level"),
            int(data.get("html", False))
        ))
