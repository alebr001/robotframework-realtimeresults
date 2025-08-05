# api/viewer/routes.py
from fastapi import Depends, APIRouter, Request, Response
from fastapi.responses import RedirectResponse
from datetime import datetime, timezone
import logging

router = APIRouter()
logger = logging.getLogger("rt.api.viewer")

def get_event_reader(request: Request):
    return request.app.state.event_reader

@router.get("/applog")
def get_applog(reader = Depends(get_event_reader)):
    return reader.get_app_logs()

@router.get("/events")
def get_events(reader = Depends(get_event_reader)):
    return reader.get_events()

@router.get("/events/clear")
def clear_events(reader = Depends(get_event_reader)):
    logger.debug("Initiating clear_events() via GET /events/clear")

    try:
        reader.clear_events()
        logger.info("Successfully cleared all events using %s", reader.__class__.__name__)
    except Exception as e:
        logger.error("Failed to clear events: %s", str(e))
        raise

    return RedirectResponse(url="/events", status_code=303)

@router.get("/elapsed")
def get_elapsed_time(reader = Depends(get_event_reader)):
    start_event = next((e for e in reader.get_events() if e['event_type'] == 'start_suite'), None)
    if not start_event:
        return {"elapsed": "00:00:00"}

    start_ts = datetime.fromisoformat(start_event["starttime"])
    now = datetime.now(timezone.utc)
    elapsed = now - start_ts
    return {"elapsed": str(elapsed).split('.')[0]}

@router.get("/")
def index():
    return {"message": "RealtimeResults API is running", "endpoints": ["/events", "/event (POST)"]}

@router.get("/favicon.ico")
def favicon():
    return Response(status_code=204)

