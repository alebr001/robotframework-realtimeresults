import sqlite3
import logging

from shared.helpers.config_loader import load_config
from shared.helpers.logger import setup_root_logging
from shared.helpers.ensure_db_schema import async_ensure_schema
from shared.sinks.sqlite_async import AsyncSqliteSink
from shared.sinks.memory_sqlite import MemorySqliteSink

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    if isinstance(event_sink, AsyncSqliteSink):
        await async_ensure_schema(db_path)
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
app.mount("/dashboard", StaticFiles(directory="dashboard", html=True), name="dashboard")

ingest_sink_type = config.get("ingest_sink_type", "asyncsqlite").lower()
db_path = config.get("sqlite_path", "eventlog.db")
strategy = config.get("backend_strategy", "db").lower()  # http_backend_listener, db, loki
listener_sink_type = config.get("listener_sink_type", "sqlite").lower()

if strategy == "sqlite":
    if listener_sink_type == "backend_http_inmemory":
        memory_sink = MemorySqliteSink()
        event_sink = memory_sink  # used for POST /event
    elif ingest_sink_type == "asyncsqlite":
        event_sink = AsyncSqliteSink(database_path=db_path)  # used for GET /events from db
    else:
        raise ValueError(f"Unsupported listener_sink_type in config: {ingest_sink_type}")
else:
    raise ValueError(f"Unsupported strategy in config: {strategy}")

@app.post("/log")
async def receive_async_event(request: Request):
    event = await request.json()
    logger.info(f"Received event: {event}")
    assert "event_type" in event, "event_type is missing from event!"
    try:
        await event_sink.async_handle_event(event)
    except Exception as e:
        logger.exception("Failed to handle event")
        return {"error": str(e)}
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
