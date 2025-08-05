from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import sqlite3
import logging

router = APIRouter()
logger = logging.getLogger("rt.api.ingest")

# Dispatch maps per endpoint
def get_dispatch_maps(event_sink):
    return {
        "log":     ({"app_log", "www_log", "debug_log"}, event_sink.handle_app_log),
        "metric":  ({"metric"}, event_sink.handle_metric),
        "event":   ({
            "start_test", "end_test", "start_suite", "end_suite",
            "start_keyword", "end_keyword", "test_step"
        }, event_sink.handle_rf_events),
        "event/log_message": ({"log_message"}, event_sink.handle_rf_log),
    }

def get_handler_by_event_type(event_type: str, sink):
    dispatch = get_dispatch_maps(sink)
    for _, (types, handler) in dispatch.items():
        if event_type in types:
            return handler
    return None

@router.post("/log")
async def receive_log_event(request: Request):
    return await handle_event_request(request, "log", allow_fallback=True)

@router.post("/metric")
async def receive_metric_event(request: Request):
    return await handle_event_request(request, "metric")

@router.post("/event")
async def receive_test_event(request: Request):
    return await handle_event_request(request, "event")

@router.post("/event/log_message")
async def receive_test_log_message(request: Request):
    return await handle_event_request(request, "event/log_message")


async def handle_event_request(request: Request, endpoint_name: str, allow_fallback: bool = False):
    event_sink = request.app.state.event_sink
    dispatch_map = get_dispatch_maps(event_sink)
    allowed_types, fallback_handler = dispatch_map.get(endpoint_name, (set(), None))

    try:
        event = await request.json()
        logger.info(f"[{endpoint_name.upper()}] Received event: {event}")
    except Exception:
        return JSONResponse(content={"error": "Invalid JSON"}, status_code=400)

    event_type = event.get("event_type")
    if not event_type:
        return JSONResponse(content={"error": f"Missing event_type for /{endpoint_name}"}, status_code=400)

    try:
        if event_type in allowed_types:
            handler = get_handler_by_event_type(event_type, event_sink)
        elif allow_fallback:
            logger.warning(f"[{endpoint_name.upper()}] Unknown event_type '{event_type}', falling back.")
            handler = fallback_handler
        else:
            return JSONResponse(content={"error": f"Invalid event_type '{event_type}' for /{endpoint_name}"}, status_code=400)

        if handler:
            await handler(event)
        else:
            raise RuntimeError("Handler unexpectedly None")
    except Exception:
        logger.error(f"[{endpoint_name.upper()}] Error handling event {event_type}.", exc_info=True)
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

    return {"received": True}
