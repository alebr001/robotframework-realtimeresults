import requests
import httpx
from .base import EventSink
from .base import AsyncEventSink

class HttpSink(EventSink):
    """
    Routes events to /metric, /log, or /event based on their event_type.
    Falls back to /log for unknown or missing event_type values.

    Intended for use in synchronous contexts like the Robot Framework listener.
    """

    def __init__(self, endpoint="http://localhost:8001", timeout=0.5):
        super().__init__()
        self.endpoint = endpoint
        self.timeout = timeout

        self.route_map = {
            # METRICS
            "metric": "/metric",

            # LOGS
            "app_log": "/log",
            "www_log": "/log",
            "debug_log": "/log",

            # TEST EVENTS
            "start_test": "/event",
            "end_test": "/event",
            "start_suite": "/event",
            "end_suite": "/event",
            "start_keyword": "/event",
            "end_keyword": "/event",
            "test_step": "/event",
            
            # RF LOG MESSAGES
            "log_message": "/event/log_message",
        }

    def _handle_event(self, data):
        event_type = data.get("event_type")
        path = self.route_map.get(event_type)

        if not path:
            self.logger.warning(
                "[HttpSink] Unknown event_type '%s'. Defaulting to /log.", event_type
            )
            path = "/log"

        try:
            requests.post(f"{self.endpoint}{path}", json=data, timeout=self.timeout)
        except requests.RequestException as e:
            self.logger.warning("[HttpSink] Failed to send %s to %s: %s", event_type, path, e)


class AsyncHttpSink(AsyncEventSink):
    """
    An asynchronous HTTP sink for sending event data as JSON to an external service.
    Designed for use in async contexts like FastAPI ingestion or log tailing.

    Events are dispatched based on their `event_type`. Unknown event types will
    fall back to the `_handle_app_log` handler.

    Routes events to /metric, /log, or /event based on their event_type.
    """

    def __init__(self, endpoint="http://localhost:8001", timeout=0.5):
        super().__init__()
        self.endpoint = endpoint
        self.timeout = timeout

        self.route_map = {
            # METRICS
            "metric": "/metric",

            # LOGS
            "app_log": "/log",
            "www_log": "/log",
            "rf_debug_log": "/log",

            # TEST EVENTS
            "start_test": "/event",
            "end_test": "/event",
            "start_suite": "/event",
            "end_suite": "/event",
            "start_keyword": "/event",
            "end_keyword": "/event",
            "log_message": "/event",
            "test_step": "/event",
        }

    async def _async_handle_event(self, data):
        event_type = data.get("event_type")
        path = self.route_map.get(event_type)

        if not path:
            self.logger.warning(
                "[AsyncHttpSink] Unknown event_type '%s'. Defaulting to /log.", event_type
            )
            path = "/log"

        try:
            async with httpx.AsyncClient() as session:
                await session.post(f"{self.endpoint}{path}", json=data, timeout=self.timeout)
        except Exception as e:
            self.logger.warning("[AsyncHttpSink] Failed to send %s to %s: %s", event_type, path, e)
