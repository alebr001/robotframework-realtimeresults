from fastapi import FastAPI, Request, Response
from fastapi.responses import RedirectResponse

from helpers.config_loader import load_config
from backend.readers.memory_reader import MemoryEventReader
from backend.readers.sqlite_reader import SqliteEventReader
from realtimelogger.sinks.sqlite import SqliteSink
from realtimelogger.sinks.memory import MemorySink

app = FastAPI()

config = load_config()
sink_type = config.get("sink_type", "sqlite").lower()

if sink_type == "memory":
    event_provider = MemoryEventReader()
    event_sink = MemorySink()
elif sink_type == "sqlite":
    db_path = config.get("sqlite_path", "eventlog.db")
    event_provider = SqliteEventReader(database_path=db_path)
    event_sink = SqliteSink(database_path=db_path)
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
    return event_provider.get_events()

@app.get("/events/clear")
def clear_events():
    event_provider.clear_events()
    return RedirectResponse(url="/events", status_code=303)

@app.get("/")
def index():
    return {"message": "RealtimeLogger API is running", "endpoints": ["/events", "/event (POST)"]}

@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)