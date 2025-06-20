import aiosqlite
from pathlib import Path
from .base import AsyncEventSink
from shared.helpers.sql_definitions import (
    CREATE_EVENTS_TABLE,
    CREATE_RF_LOG_MESSAGE_TABLE,
    CREATE_APP_LOG_TABLE,
    CREATE_METRIC_TABLE,
    INSERT_EVENT,
    INSERT_RF_LOG_MESSAGE,
    INSERT_APP_LOG,
    INSERT_METRIC,
)

# AsyncSqliteSink: intended for general asynchronous logging such as application logs and metrics.
# Supports event types: app_logs, and metrics.
# For Robot Framework listener, use SqliteSink instead.

class AsyncSqliteSink(AsyncEventSink):
    def __init__(self, database_path="eventlog.db"):
        super().__init__()
        self.database_path = Path(database_path)
        self.dispatch_map = {
            "start_test": self._insert_event,
            "end_test": self._insert_event,
            "start_suite": self._insert_event,
            "end_suite": self._insert_event,
            "log_message": self._handle_log_message,
            "app_log": self._handle_app_log,
            "metric": self._handle_metric,
        }

    async def _initialize_database(self):
        try:
            async with aiosqlite.connect(self.database_path) as db:
                await db.execute(CREATE_EVENTS_TABLE)
                await db.execute(CREATE_RF_LOG_MESSAGE_TABLE)
                await db.execute(CREATE_APP_LOG_TABLE)
                await db.execute(CREATE_METRIC_TABLE)
                await db.commit()
        except Exception as e:
            self.logger.warning("[SQLITE_ASYNC] Failed to initialize DB: %s", e)
            raise

    async def _handle_event(self, data):
        event_type = data.get("event_type")
        handler = self.dispatch_map.get(event_type)
        if handler:
            await handler(data)
        else:
            self.logger.warning("[SQLITE_ASYNC] No handler for event_type: %s", event_type)

    async def _handle_log_message(self, data):
        try:
            async with aiosqlite.connect(self.database_path) as db:
                await db.execute(INSERT_RF_LOG_MESSAGE, (
                    data.get("testid"),
                    data.get("timestamp"),
                    data.get("level"),
                    data.get("message"),
                    int(bool(data.get("html"))),
                ))
                await db.commit()
        except Exception as e:
            self.logger.warning("[SQLITE_ASYNC] Failed to insert RF log: %s", e)

    async def _handle_app_log(self, data):
        try:
            async with aiosqlite.connect(self.database_path) as db:
                await db.execute(INSERT_APP_LOG, (
                    data.get("timestamp"),
                    data.get("message"),
                    data.get("source"),
                ))
                await db.commit()
        except Exception as e:
            self.logger.warning("[SQLITE_ASYNC] Failed to insert app log: %s", e)

    async def _handle_metric(self, data):
        try:
            async with aiosqlite.connect(self.database_path) as db:
                await db.execute(INSERT_METRIC, (
                    data.get("timestamp"),
                    data.get("name"),
                    data.get("value"),
                    data.get("unit"),
                    data.get("source"),
                ))
                await db.commit()
        except Exception as e:
            self.logger.warning("[SQLITE_ASYNC] Failed to insert metric: %s", e)

    async def _insert_event(self, data):
        tags = data.get("tags", [])
        if not isinstance(tags, list):
            tags = [str(tags)]
        tag_string = ",".join(str(tag) for tag in tags)

        try:
            async with aiosqlite.connect(self.database_path) as db:
                await db.execute(INSERT_EVENT, (
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
                await db.commit()
        except Exception as e:
            self.logger.warning("[SQLITE_ASYNC] Failed to insert event: %s", e)