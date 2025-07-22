import asyncpg
import shared.helpers.sql_definitions as sql_definitions
from shared.helpers.ensure_db_schema import async_ensure_schema
from .base import AsyncEventSink

from shared.helpers.config_loader import load_config

class AsyncPostgresSink(AsyncEventSink):
    def __init__(self, database_url=None):
        super().__init__()
        config = load_config()
        self.database_url = database_url or config.get("database_url")
        self.dispatch_map = {
            "app_log": self._handle_app_log,
            "www_log": self._handle_app_log,  # Alias for app_log
            "metric": self._handle_metric,
            "rf_output_xml": self._handle_app_log,  # Robot Framework output XML logs
            "rf_debug_log": self._handle_app_log,  # Robot Framework debug logs
        }
        self.logger.debug("Async sink writing to PostgreSQL: %s", self.database_url)

    async def _initialize_database(self):
        try:
            await async_ensure_schema(self.database_url)
        except Exception as e:
            self.logger.warning("[POSTGRES_ASYNC] Failed to initialize DB: %s", e)
            raise

    def handle_event(self, data):
        raise NotImplementedError("This function is not implemented.")
    
    async def _async_handle_event(self, data):
        event_type = data.get("event_type")
        handler = self.dispatch_map.get(event_type)
        if handler:
            await handler(data, sql_definitions.metric_columns)
        else:
            self.logger.warning("[POSTGRES_ASYNC] No handler for event_type: %s", event_type)

    async def _handle_app_log(self, data):
        self.logger.debug("[POSTGRES_ASYNC] Inserting app_log: %s", data)
        try:
            values = [data.get(col_name) for col_name, _ in sql_definitions.app_log_columns]
            conn = await asyncpg.connect(self.database_url)
            async with conn.transaction():
                await conn.execute(sql_definitions.INSERT_APP_LOG, *values)
            await conn.close()
        except Exception as e:
            self.logger.warning("[POSTGRES_ASYNC] Failed to insert app log: %s", e)

    async def _handle_metric(self, data):
        self.logger.debug("[POSTGRES_ASYNC] Inserting metric: %s", data)
        try:
            values = [data.get(col_name) for col_name, _ in sql_definitions.metric_columns]
            conn = await asyncpg.connect(self.database_url)
            async with conn.transaction():
                await conn.execute(sql_definitions.INSERT_METRIC, *values)
            await conn.close()
        except Exception as e:
            self.logger.warning("[POSTGRES_ASYNC] Failed to insert metric: %s", e)
