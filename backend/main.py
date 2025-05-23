import sqlite3
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse

from backend.readers.sqlite_reader import SqliteEventReader
from realtimelogger.sinks.sqlite import SqliteSink
from backend.sinks.memory_sqlite import MemorySqliteSink
from helpers.config_loader import load_config
from helpers.logger import setup_logging
from fastapi.staticfiles import StaticFiles
import logging

logger = logging.getLogger(__name__)
config = load_config()
setup_logging(config.get("log_level", "info"))

logger.debug("----------------------------")
logger.debug("Starting FastAPI application")
logger.debug("----------------------------")

app = FastAPI()
app.mount("/dashboard", StaticFiles(directory="backend/static", html=True), name="static")

sink_type = config.get("sink_type", "sqlite").lower()
db_path = config.get("sqlite_path", "eventlog.db")
strategy = config.get("sink_strategy", "local")

if strategy == "http":
    if sink_type == "sqlite":
        memory_sink = MemorySqliteSink()
        event_sink = memory_sink  # used for POST /event
        event_reader = SqliteEventReader(conn=memory_sink.get_connection())
elif strategy == "local":        
    if sink_type == "sqlite":
        event_sink = SqliteSink(database_path=db_path)
        event_reader = SqliteEventReader(database_path=db_path)
else:
    raise ValueError(f"Unsupported sink_type in config: {sink_type}")

@app.post("/event")
async def receive_event(request: Request):
    event = await request.json()
    try:
        event_sink.handle_event(event)
    except Exception as e:
        return {"error": str(e)}
    return {"received": True}

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

@app.get("/")
def index():
    return {"message": "RealtimeLogger API is running", "endpoints": ["/events", "/event (POST)"]}

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