import aiosqlite
from .db_base import BaseIngestSink
from shared.helpers.ensure_db_schema import async_ensure_schema
import shared.helpers.sql_definitions as sql_definitions


class AsyncSqliteSink(BaseIngestSink):
    """
    Asynchronous SQLite sink for application logs, metrics, and test events.

    Each public handler method corresponds to a distinct event category
    and is called explicitly by the ingest API based on the event_type.
    For Robot Framework listener to DB directly, use SqliteSink instead.
    """

    def __init__(self, database_url="sqlite:///eventlog.db"):
        super().__init__()

        # Strip 'sqlite:///' prefix if present
        if database_url.startswith("sqlite:///"):
            self.database_path = database_url.replace("sqlite:///", "", 1)
        else:
            self.database_path = database_url

        self.logger.debug(f"[SQLITE_ASYNC] Sink writing to: {self.database_path}")

    # call from ingest main.py to initialize the database schema
    async def initialize_database(self):
        """Initialize schema if not yet created."""
        try:
            await async_ensure_schema(self.database_path)
        except Exception as e:
            self.logger.warning("[SQLITE_ASYNC] Failed to initialize DB: %s", e)
            raise
    
    async def handle_app_log(self, data):
        """Insert application log event into 'app_logs' table."""
        self.logger.debug("[SQLITE_ASYNC] Inserting app_log: %s", data)
        try:
            async with aiosqlite.connect(self.database_path) as db:
                values = [self.make_sql_safe(data.get(col)) for col, _ in sql_definitions.app_log_columns]
                await db.execute(sql_definitions.INSERT_APP_LOG, values)
                await db.commit()
        except Exception as e:
            self.logger.warning("[SQLITE_ASYNC] Failed to insert app log: %s", e)

    async def handle_metric(self, data):
        """Insert metric data into 'metrics' table."""
        self.logger.debug("[SQLITE_ASYNC] Inserting metric: %s", data)
        try:
            async with aiosqlite.connect(self.database_path) as db:
                values = [self.make_sql_safe(data.get(col)) for col, _ in sql_definitions.metric_columns]
                await db.execute(sql_definitions.INSERT_METRIC, values)
                await db.commit()
        except Exception as e:
            self.logger.warning("[SQLITE_ASYNC] Failed to insert metric: %s", e)

    async def handle_rf_events(self, data):
        """Insert Robot Framework test event into 'rf_events' table."""
        self.logger.debug("[SQLITE_ASYNC] Inserting RF event: %s", data)
        try:
            async with aiosqlite.connect(self.database_path) as db:
                # Convert all list, dict or bool values in `data` to JSON strings 
                # This is necessary specifically for tags
                values = [self.make_sql_safe(data.get(col)) for col, _ in sql_definitions.event_columns] # e.g. col = tags, _ = "TEXT"
                await db.execute(sql_definitions.INSERT_EVENT, values)
                await db.commit()
        except Exception as e:
            self.logger.warning("[SQLITE_ASYNC] Failed to insert RF event: %s", e)

    async def handle_rf_log(self, data):
        """Insert Robot Framework log_message into 'rf_log_messages' table."""
        self.logger.debug("[SQLITE_ASYNC] Inserting RF log message: %s", data)
        try:
            async with aiosqlite.connect(self.database_path) as db:
                values = [self.make_sql_safe(data.get(col)) for col, _ in sql_definitions.rf_log_columns]
                await db.execute(sql_definitions.INSERT_RF_LOG_MESSAGE, values)
                await db.commit()
        except Exception as e:
            self.logger.warning("[SQLITE_ASYNC] Failed to insert RF log message: %s", e)
