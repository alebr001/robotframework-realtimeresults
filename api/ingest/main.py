import sqlite3
import logging
import sys

from shared.helpers.config_loader import load_config
from shared.helpers.logger import setup_root_logging
from shared.helpers.ensure_db_schema import async_ensure_schema

from shared.sinks.sqlite_async import AsyncSqliteSink
from shared.sinks.memory_sqlite import MemorySqliteSink
from shared.sinks.postgres_async import AsyncPostgresSink

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    if isinstance(event_sink, AsyncSqliteSink):
        try:
            await async_ensure_schema(config.get("database_url", "sqlite:///eventlog.db"))
        except Exception as e:
            print(f"[FATAL] Could not initialize database: {e}")
            sys.exit(1)
    yield

config = load_config()
setup_root_logging(config.get("log_level", "info"))

logger = logging.getLogger("rt.api.ingest")
component_level_logging = config.get("log_level_cli")
if component_level_logging:
    logger.setLevel(getattr(logging, component_level_logging.upper(), logging.INFO))

logger.debug("----------------------------")
logger.debug("Starting FastAPI application")
logger.debug("----------------------------")

app = FastAPI(lifespan=lifespan)

ingest_sink_type = config.get("ingest_sink_type", "async").lower()
database_url = config.get("database_url", "sqlite:///eventlog.db")

if database_url.startswith("sqlite:///"):
    # set the sink type. If Listener uses inmemory db then use that as event_sink otherwise use ingest_sink_type
    if "inmemory" in database_url:
        memory_sink = MemorySqliteSink()
        event_sink = memory_sink  # used for POST /event
    elif ingest_sink_type == "async":
        event_sink = AsyncSqliteSink(database_url=database_url)  # used for GET /events from db
    else:
        raise ValueError(f"Unsupported sink_type in config: {ingest_sink_type}")
elif database_url.startswith(("postgresql://", "postgres://")):
    event_sink = AsyncPostgresSink(database_url=database_url)
else:
    raise ValueError(f"Unsupported databasetype in database_url in config, prefix with sqlite:/// or postgres://")

@app.post("/log")
async def receive_async_event(request: Request):
    event = await request.json()
    logger.info(f"Received event: {event}")
    if "event_type" not in event:
        return JSONResponse(content={"error": "event_type is missing"}, status_code=400)
    try:
        await event_sink.async_handle_event(event)
    except Exception as e:
        logger.error("Unexpected error while handling event", exc_info=True)
        return JSONResponse(content={"error": "Unexpected error"}, status_code=500)
    return {"received": True}

@app.get("/log")
async def log_get_info():
    return {"status": "log endpoint expects POST with JSON payload"}

# not handled
@app.post("/event")
async def receive_event(request: Request):
    event = await request.json()
    try:
        event_sink.handle_event(event)
    except Exception as e:
        return {"error": str(e)}
    return {"received": True}

@app.exception_handler(sqlite3.OperationalError)
async def sqlite_error_handler(request: Request, exc: sqlite3.OperationalError):
    logger.warning("Database unavailable during request to %s: %s", request.url.path, str(exc))
    return JSONResponse(
        status_code=503,
        content={"detail": f"Database error: {str(exc)}"}
    )
