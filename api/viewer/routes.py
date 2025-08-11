from fastapi import Depends, APIRouter, Request, Response
from fastapi.responses import RedirectResponse, StreamingResponse
import asyncio, json, logging
from datetime import datetime, timezone

router = APIRouter()
logger = logging.getLogger("rt.api.viewer")


def get_event_reader(request: Request):
    return request.app.state.event_reader


def get_event_manager(request: Request):
    return request.app.state.event_manager


@router.get("/events/stream")
async def stream_events(
    request: Request,
    reader = Depends(get_event_reader),
    event_manager = Depends(get_event_manager)
):
    tenant_id = getattr(request.state, "tenant_id", "default")

    async def event_generator():
        client_queue = asyncio.Queue(maxsize=100)
        await event_manager.add_client(tenant_id, client_queue)
        try:
            yield "retry: 5000\n\n"

            # Initial snapshot: last 50 events of this tenant
            latest = reader.get_latest_event_id(tenant_id)
            recent_events = reader.get_events_since(max(0, latest - 50), tenant_id=tenant_id)
            for event in recent_events:
                yield f"data: {json.dumps(event)}\n\n"

            while True:
                try:
                    data = await asyncio.wait_for(client_queue.get(), timeout=30.0)
                    yield data
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
                except asyncio.CancelledError:
                    break
        except Exception as e:
            logger.error(f"Error in event stream: {e}")
        finally:
            await event_manager.remove_client(tenant_id, client_queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/applog/stream")
async def stream_app_logs(
    request: Request,
    reader = Depends(get_event_reader),
    event_manager = Depends(get_event_manager)
):
    tenant_id = getattr(request.state, "tenant_id", "default")

    async def log_generator():
        client_queue = asyncio.Queue(maxsize=100)
        await event_manager.add_app_log_client(tenant_id, client_queue)
        try:
            yield "retry: 5000\n\n"

            logs = reader.get_app_logs(tenant_id=tenant_id, limit=50)
            # newest first -> stream oldest first for nicer UX
            for rec in reversed(logs):
                yield f"data: {json.dumps(rec)}\n\n"

            while True:
                try:
                    data = await asyncio.wait_for(client_queue.get(), timeout=30.0)
                    yield data
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
                except asyncio.CancelledError:
                    break
        except Exception as e:
            logger.error(f"Error in app log stream: {e}")
        finally:
            await event_manager.remove_app_log_client(tenant_id, client_queue)

    return StreamingResponse(
        log_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/events/broadcast")
async def broadcast_event(
    request: Request,
    event_data: dict,
    event_manager = Depends(get_event_manager)
):
    tenant_id = getattr(request.state, "tenant_id", "default")
    await event_manager.broadcast_event(tenant_id, event_data)
    return {"status": "broadcasted"}


@router.post("/applog/broadcast")
async def broadcast_app_log(
    request: Request,
    log_data: dict,
    event_manager = Depends(get_event_manager)
):
    tenant_id = getattr(request.state, "tenant_id", "default")
    await event_manager.broadcast_app_log(tenant_id, log_data)
    return {"status": "broadcasted"}


@router.get("/events/clear")
def clear_events(reader = Depends(get_event_reader)):
    logger.debug("Initiating clear_events() via GET /events/clear")
    try:
        reader.clear_events()  # consider making this tenant-aware too
        logger.info("Successfully cleared all events using %s", reader.__class__.__name__)
    except Exception as e:
        logger.error("Failed to clear events: %s", str(e))
        raise
    return RedirectResponse(url="/dashboard", status_code=303)


@router.get("/elapsed")
def get_elapsed_time(
    request: Request,
    reader = Depends(get_event_reader)
):
    tenant_id: str = getattr(request.state, "tenant_id", "default")

    # Find start_suite for this tenant
    start_event = next(
        (e for e in reader.get_events_since(0, tenant_id=tenant_id)
         if e.get("event_type") == "start_suite"),
        None
    )
    if not start_event or not start_event.get("starttime"):
        return {"elapsed": "00:00:00"}

    # Parse ISO; if naive, assume UTC
    start_ts = datetime.fromisoformat(start_event["starttime"])
    if start_ts.tzinfo is None:
        start_ts = start_ts.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    elapsed = now - start_ts
    return {"elapsed": str(elapsed).split(".")[0]}

@router.get("/status")
def get_status(
    event_manager = Depends(get_event_manager),
):
    return {
        "message": "RealtimeResults API is running",
        "clients": event_manager.get_client_count(),
        "endpoints": ["/events/stream", "/applog/stream", "/events/clear", "/dashboard"],
    }


@router.get("/")
def index():
    return RedirectResponse(url="/dashboard", status_code=303)


@router.get("/favicon.ico")
def favicon():
    return Response(status_code=204)
