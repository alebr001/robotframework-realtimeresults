import aiosqlite
from pathlib import Path

from shared.helpers.ensure_db_schema import async_ensure_schema
from .base import AsyncEventSink
import shared.helpers.sql_definitions as sql_definitions

# AsyncSqliteSink: intended for general asynchronous logging such as application logs and metrics.
# Supports event types: app_logs, and metrics.
# For Robot Framework listener, use SqliteSink instead.

class AsyncSqliteSink(AsyncEventSink):
    def __init__(self, database_url="sqlite:///eventlog.db"):
        super().__init__()

        # Strip 'sqlite:///' prefix if present
        if database_url.startswith("sqlite:///"):
            database_url = database_url.replace("sqlite:///", "", 1)
        else:
            database_url = database_url


        self.database_path = Path(database_url)
        self.dispatch_map = {
            "app_log": self._handle_app_log,
            "www_log": self._handle_app_log,
            "metric": self._handle_metric,
            "rf_output_xml": self._handle_app_log, # Robot Framework output XML logs
            "rf_debug_log": self._handle_app_log, # Robot Framework debug logs
            "rf_debug": self._handle_app_log, # Robot Framework debug logs
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
                values = [data.get(col) for col, _ in sql_definitions.app_log_columns]
                await db.execute(sql_definitions.INSERT_APP_LOG, values)
                await db.commit()
        except Exception as e:
            self.logger.warning("[SQLITE_ASYNC] Failed to insert app log: %s", e)

    async def _handle_metric(self, data):
        self.logger.debug("[SQLITE_ASYNC] Inserting metric: %s", data)
        try:
            async with aiosqlite.connect(self.database_path) as db:
                values = [data.get(col) for col, _ in sql_definitions.metric_columns]
                await db.execute(sql_definitions.INSERT_METRIC, values)
                await db.commit()
        except Exception as e:
            self.logger.warning("[SQLITE_ASYNC] Failed to insert metric: %s", e)
