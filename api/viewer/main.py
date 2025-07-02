import sqlite3
import logging

from shared.helpers.config_loader import load_config
from shared.helpers.logger import setup_root_logging
from shared.helpers.ensure_db_schema import ensure_schema

from shared.sinks.memory_sqlite import MemorySqliteSink
from api.viewer.readers.sqlite_reader import SqliteReader

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime, timezone



config = load_config()
ensure_schema(config.get("sqlite_path", "eventlog.db"))
setup_root_logging(config.get("log_level", "info"))

logger = logging.getLogger("rt.api.viewer")
component_level_logging = config.get("log_level_cli")
if component_level_logging:
    logger.setLevel(getattr(logging, component_level_logging.upper(), logging.INFO))

logger.debug("----------------------------")
logger.debug("Starting FastAPI application")
logger.debug("----------------------------")

app = FastAPI()
app.mount("/dashboard", StaticFiles(directory="dashboard", html=True), name="dashboard")

listener_sink_type = config.get("listener_sink_type", "sqlite").lower()
db_path = config.get("sqlite_path", "eventlog.db")
strategy = config.get("backend_strategy", "db").lower()  # http_backend_listener, db, loki

if strategy == "sqlite":
    if listener_sink_type == "backend_http_inmemory":
        event_reader = SqliteReader(conn=MemorySqliteSink().get_connection()) # used for GET /events from db
    if listener_sink_type == "sqlite":
        event_reader = SqliteReader(database_path=db_path) # used for GET /events from db
    else:
        raise ValueError(f"Unsupported listener_sink_type in config: {listener_sink_type}")
else:
    raise ValueError(f"Unsupported strategy in config: {strategy}")

@app.get("/applog")
def get_applog():
    return event_reader.get_app_logs()

@app.get("/events")
def get_events():
    return event_reader.get_events()
    
@app.get("/events/clear")
def clear_events():
    logger.debug("Initiating clear_events() via GET /events/clear")

    try:
        event_reader.clear_events()
        logger.info("Successfully cleared all events using %s", event_reader.__class__.__name__)
    except Exception as e:
        logger.error("Failed to clear events: %s", str(e))
        raise

    return RedirectResponse(url="/events", status_code=303)

@app.get("/elapsed")
def get_elapsed_time():
    start_event = next((e for e in event_reader.get_events() if e['event_type'] == 'start_suite'), None)
    if not start_event:
        return {"elapsed": "00:00:00"}

    start_ts = datetime.fromisoformat(start_event["timestamp"])
    now = datetime.now(timezone.utc)
    elapsed = now - start_ts
    return {"elapsed": str(elapsed).split('.')[0]} 

@app.get("/")
def index():
    return {"message": "RealtimeResults API is running", "endpoints": ["/events", "/event (POST)"]}

@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)

@app.exception_handler(sqlite3.OperationalError)
async def sqlite_error_handler(request: Request, exc: sqlite3.OperationalError):
    logger.warning("Database unavailable during request to %s: %s", request.url.path, str(exc))
    return JSONResponse(
        status_code=503,
        content={"detail": f"Database error: {str(exc)}"}
    )
