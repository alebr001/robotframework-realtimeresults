from fastapi import FastAPI
from shared.helpers.config_loader import load_config
from shared.helpers.logger import setup_root_logging
from shared.sinks.base import AsyncEventSink
from api.ingest.sinks.sqlite_async import AsyncSqliteSink
from api.ingest.sinks.postgres_async import AsyncPostgresSink
from api.ingest.routes import router as ingest_routes
from contextlib import asynccontextmanager

# Load configuration and setup root logging
config = load_config()
setup_root_logging(config.get("log_level", "info"))

# Determine database type and create appropriate sink instance
database_url = config.get("database_url", "sqlite:///eventlog.db")
ingest_sink_type = config.get("ingest_sink_type", "async").lower()

# For SQLite, only 'async' sink is currently supported
if database_url.startswith("sqlite:///"):
    if ingest_sink_type == "async":
        event_sink = AsyncSqliteSink(database_url=database_url)
    else:
        raise ValueError(f"Unsupported sink_type in config: {ingest_sink_type}")
# For PostgreSQL, async sink is always used
elif database_url.startswith(("postgresql://", "postgres://")):
    event_sink = AsyncPostgresSink(database_url=database_url)
else:
    raise ValueError("Unsupported database_url: must start with sqlite:/// or postgres://")

# Lifespan context used to initialize the database on app startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    if isinstance(event_sink, AsyncEventSink):
        try:
            await event_sink.initialize_database()
        except Exception as e:
            print(f"[FATAL] Could not initialize database: {e}")
            import sys
            sys.exit(1)
    yield

def create_app() -> FastAPI:
    """
    This factory function builds the ingest FastAPI app.

    Unlike the viewer API, this ingest API requires the event_sink to be 
    fully initialized during app creation. That's because:
    
    - The sink is used directly by all endpoint handlers.
    - The sink is initialized in the app's lifespan context before accepting requests.
    - Routes depend on dispatching by event_type to specific sink handlers.
    
    In contrast, the viewer app only needs a database reader (event_reader),
    which can be injected later (e.g. in main.py or tests). That makes the 
    viewer create_app() simpler and more decoupled from infrastructure.
    """
    app = FastAPI(lifespan=lifespan)
    app.include_router(ingest_routes)
    app.state.event_sink = event_sink
    return app
