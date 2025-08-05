import asyncpg
from .db_base import BaseIngestSink
import shared.helpers.sql_definitions as sql_definitions
from shared.helpers.ensure_db_schema import async_ensure_schema

from shared.helpers.config_loader import load_config

class AsyncPostgresSink(BaseIngestSink):
    """
    Asynchronous PostgreSQL sink for application logs, metrics, and Robot Framework events.

    All dispatching is expected to be done by the ingest API.
    Each handler function corresponds to a single use case.
    """

    def __init__(self, database_url=None):
        super().__init__()
        config = load_config()
        self.database_url = database_url or config.get("database_url")
        self.logger.debug("Async sink writing to PostgreSQL: %s", self.database_url)

    # call from ingest main.py to initialize the database schema
    async def initialize_database(self):
        try:
            await async_ensure_schema(self.database_url)
        except Exception as e:
            self.logger.warning("[POSTGRES_ASYNC] Failed to initialize DB: %s", e)
            raise

    async def handle_app_log(self, data):
        """Insert app-level log data into 'app_logs' table."""
        self.logger.debug("[POSTGRES_ASYNC] Inserting app_log: %s", data)
        conn = None
        try:
            values = [self.make_sql_safe(data.get(col)) for col, _ in sql_definitions.app_log_columns]
            conn = await asyncpg.connect(self.database_url)
            async with conn.transaction():
                await conn.execute(sql_definitions.INSERT_APP_LOG, *values)
        except Exception as e:
            self.logger.warning("[POSTGRES_ASYNC] Failed to insert app log: %s", e)
        finally:
            if conn:
                await conn.close()


    async def handle_metric(self, data):
        """Insert metric data into 'metrics' table."""
        self.logger.debug("[POSTGRES_ASYNC] Inserting metric: %s", data)
        conn = None
        try:
            values = [self.make_sql_safe(data.get(col)) for col, _ in sql_definitions.metric_columns]
            conn = await asyncpg.connect(self.database_url)
            async with conn.transaction():
                await conn.execute(sql_definitions.INSERT_METRIC, *values)
        except Exception as e:
            self.logger.warning("[POSTGRES_ASYNC] Failed to insert metric: %s", e)
        finally:
            if conn:
                await conn.close()

    async def handle_rf_events(self, data):
        """Insert Robot Framework event into 'rf_events' table."""
        self.logger.debug("[POSTGRES_ASYNC] Inserting RF event: %s", data)
        conn = None
        try:
            values = [self.make_sql_safe(data.get(col)) for col, _ in sql_definitions.event_columns]
            conn = await asyncpg.connect(self.database_url)
            async with conn.transaction():
                await conn.execute(sql_definitions.INSERT_EVENT, *values)
        except Exception as e:
            self.logger.warning("[POSTGRES_ASYNC] Failed to insert RF event: %s", e)
        finally:
            if conn:
                await conn.close()

    async def handle_rf_log(self, data):
        """Insert Robot Framework log message into 'rf_log_messages' table."""
        self.logger.debug("[POSTGRES_ASYNC] Inserting RF log message: %s", data)
        conn = None
        try:
            values = [self.make_sql_safe(data.get(col)) for col, _ in sql_definitions.rf_log_columns]
            conn = await asyncpg.connect(self.database_url)
            async with conn.transaction():
                await conn.execute(sql_definitions.INSERT_RF_LOG_MESSAGE, *values)
        except Exception as e:
            self.logger.warning("[POSTGRES_ASYNC] Failed to insert RF log message: %s", e)
        finally:
            if conn:
                await conn.close()

