import sqlite3
import logging
import sys

from shared.helpers.config_loader import load_config
from shared.helpers.logger import setup_root_logging

from shared.sinks.base import AsyncEventSink
from api.ingest.sinks.sqlite_async import AsyncSqliteSink
from api.ingest.sinks.postgres_async import AsyncPostgresSink

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    if isinstance(event_sink, AsyncEventSink):
        try:
            await event_sink.initialize_database()
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
    if ingest_sink_type == "async":
        event_sink = AsyncSqliteSink(database_url=database_url)
    else:
        raise ValueError(f"Unsupported sink_type in config: {ingest_sink_type}")
elif database_url.startswith(("postgresql://", "postgres://")):
    event_sink = AsyncPostgresSink(database_url=database_url)
else:
    raise ValueError("Unsupported databasetype in database_url in config, prefix with sqlite:/// or postgres://")

# Dispatch maps per endpoint
log_event_types = ({"app_log", "www_log", "debug_log"}, event_sink.handle_app_log)
metric_event_types = ({"metric"}, event_sink.handle_metric)
rf_event_types = ({
    "start_test", "end_test", "start_suite", "end_suite",
    "start_keyword", "end_keyword", "test_step"
}, event_sink.handle_rf_events) 
rf_log_event_types = ({"log_message"}, event_sink.handle_rf_log)

def get_handler_by_event_type(event_type: str):
    if event_type in log_event_types[0]: return log_event_types[1]
    elif event_type in metric_event_types[0]: return metric_event_types[1]
    elif event_type in rf_event_types[0]: return rf_event_types[1]
    elif event_type in rf_log_event_types[0]: return rf_log_event_types[1]
    else:
        return None

@app.post("/log")
async def receive_log_event(request: Request):
    return await handle_event_request(request, log_event_types, "log", allow_fallback=True)

@app.post("/metric")
async def receive_metric_event(request: Request):
    return await handle_event_request(request, metric_event_types, "metric")

@app.post("/event")
async def receive_test_event(request: Request):
    return await handle_event_request(request, rf_event_types, "event")

@app.post("/event/log_message")
async def receive_test_log_message(request: Request):
    return await handle_event_request(request, rf_log_event_types, "event/log_message")


@app.exception_handler(sqlite3.OperationalError)
async def sqlite_error_handler(request: Request, exc: sqlite3.OperationalError):
    logger.warning("Database unavailable during request to %s: %s", request.url.path, str(exc))
    return JSONResponse(
        status_code=503,
        content={"detail": f"Database error: {str(exc)}"}
    )

async def handle_event_request(request: Request, dispatch_tuple, endpoint_name: str, allow_fallback: bool = False ):
    # Check if json is valid
    try:
        event = await request.json()
        logger.info(f"[{endpoint_name.upper()}] Received event: {event}")
    except Exception:
        return JSONResponse(content={"error": "Invalid JSON"}, status_code=400)

    # Check if eventtype is present
    event_type = event.get("event_type")
    if not event_type:
        return JSONResponse(
            content={"error": f"Missing event_type for /{endpoint_name}"},
            status_code=400,
        )

    allowed_types, fallback_handler = dispatch_tuple
    try:
        if event_type in allowed_types:
            handler = get_handler_by_event_type(event_type)
        elif allow_fallback:
            logger.warning(f"[{endpoint_name.upper()}] Unknown event_type '{event_type}', falling back.")
            handler = fallback_handler
        else:
            return JSONResponse(
                content={"error": f"Invalid event_type '{event_type}' for /{endpoint_name}"},
                status_code=400,
            )
        # here for instance log_event_types[1] is triggered
        await handler(event)
    except Exception:
        logger.error(f"[{endpoint_name.upper()}] Error handling event {event_type}.", exc_info=True)
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

    return {"received": True}