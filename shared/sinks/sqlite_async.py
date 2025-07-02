import aiosqlite
from pathlib import Path

from shared.helpers.ensure_db_schema import async_ensure_schema
from .base import AsyncEventSink
from shared.helpers.sql_definitions import (
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
            "app_log": self._handle_app_log,
            "www_log": self._handle_app_log,  # Alias for app_log
            "metric": self._handle_metric,
        }
        self.logger.debug("Async sink writing to: %s", self.database_path.resolve())

    async def _initialize_database(self):
        try:
            await async_ensure_schema(self.database_path)
        except Exception as e:
            self.logger.warning("[SQLITE_ASYNC] Failed to initialize DB: %s", e)
            raise

    def handle_event(self, data):
        raise NotImplementedError("This function is not implemented.")
    
    async def _async_handle_event(self, data):
        event_type = data.get("event_type")
        handler = self.dispatch_map.get(event_type)
        if handler:
            await handler(data)
        else:
            self.logger.warning("[SQLITE_ASYNC] No handler for event_type: %s", event_type)

    async def _handle_app_log(self, data):
        self.logger.debug("[SQLITE_ASYNC] Inserting app_log: %s", data)
        try:
            async with aiosqlite.connect(self.database_path) as db:
                await db.execute(INSERT_APP_LOG, (
                    data.get("timestamp"),
                    data.get("event_type"),
                    data.get("source"),
                    data.get("message"),
                    data.get("level")
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
                    data.get("source")
                ))
                await db.commit()
        except Exception as e:
            self.logger.warning("[SQLITE_ASYNC] Failed to insert metric: %s", e)
