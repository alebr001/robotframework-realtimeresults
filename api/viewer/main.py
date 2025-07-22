import sqlite3
import logging
import sys

from shared.helpers.config_loader import load_config
from shared.helpers.logger import setup_root_logging
from shared.helpers.ensure_db_schema import ensure_schema

from shared.sinks.memory_sqlite import MemorySqliteSink
from api.viewer.readers.sqlite_reader import SqliteReader
from api.viewer.readers.postgres_reader import PostgresReader

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime, timezone

config = load_config()

setup_root_logging(config.get("log_level", "info"))

logger = logging.getLogger("rt.api.viewer")
component_level_logging = config.get("log_level_cli")
if component_level_logging:
    logger.setLevel(getattr(logging, component_level_logging.upper(), logging.INFO))

try:
    ensure_schema(config.get("database_url", "sqlite:///eventlog.db"))
except Exception as e:
    logger.fatal(f"Could not initialize database: {e}")
    sys.exit(1)
    
logger.debug("----------------------------")
logger.debug("Starting FastAPI application")
logger.debug("----------------------------")

app = FastAPI()
app.mount("/dashboard", StaticFiles(directory="dashboard", html=True), name="dashboard")

database_url = config.get("database_url", "sqlite:///eventlog.db")

if database_url.startswith("sqlite:///"):
    if "inmemory" in database_url:
        event_reader = SqliteReader(conn=MemorySqliteSink().get_connection()) # used for GET /events from db
    else:
        event_reader = SqliteReader(database_url=database_url) # used for GET /events from db
elif database_url.startswith(("postgresql://", "postgres://")):
    event_reader = PostgresReader(database_url=database_url)
else:
    raise ValueError(f"Unsupported databasetype in database_url in config, prefix with sqlite:/// or postgres://")

@app.get("/applog")
def get_applog():
    return event_reader.get_app_logs()

@app.get("/events")
def get_events():
    return event_reader.get_events()
    
# todo should this move to ingest? Viewer does delete, separation of concerns    
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
