import sqlite3
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse

from helpers.config_loader import load_config
from backend.readers.sqlite_reader import SqliteEventReader
from realtimelogger.sinks.sqlite import SqliteSink
from backend.sinks.memory_sqlite import MemorySqliteSink

app = FastAPI()

config = load_config()
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
        event_sink.handle_event(event.get("event_type", "unknown"), event)
    except Exception as e:
        return {"error": str(e)}
    return {"received": True}

@app.get("/events")
def get_events():
    return event_reader.get_events()
    
@app.get("/events/clear")
def clear_events():
    event_reader.clear_events()
    return RedirectResponse(url="/events", status_code=303)

@app.get("/")
def index():
    return {"message": "RealtimeLogger API is running", "endpoints": ["/events", "/event (POST)"]}

@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)

@app.exception_handler(sqlite3.OperationalError)
async def sqlite_error_handler(request: Request, exc: sqlite3.OperationalError):
    return JSONResponse(
        status_code=503,
        content={"detail": f"Database error: {str(exc)}"}
    )