# realtimeresults/sinks/http.py
import httpx
import requests
from .base import EventSink, AsyncEventSink

class HttpSink(EventSink):
    """
    A synchronous HTTP sink that can be used in synchronous contexts
    like the Robot Framework listener. It sends events as JSON payloads
    via a POST request.
    """
    def __init__(self, endpoint="http://localhost:8001", timeout=0.5):
        super().__init__()
        self.endpoint = endpoint
        self.timeout = timeout


    def _handle_event(self, data):
        payload = dict(data)  # shallow copy
        try:
            requests.post(f"{self.endpoint}/event", json=payload, timeout=self.timeout)
        except requests.RequestException as e:
            self.logger.warning(f"Failed to post event to {self.endpoint}: {e}")


class AsyncHttpSink(AsyncEventSink):
    """
    An asynchronous HTTP sink that can be used in async environments,
    such as log tailing or FastAPI-based ingestion.
    """
    def __init__(self, endpoint="http://localhost:8001", timeout=0.5):
        super().__init__()
        self.endpoint = endpoint
        self.timeout = timeout

    async def _async_handle_event(self, data):
        payload = dict(data)  # shallow copy
        try:
            async with httpx.AsyncClient() as session:
                await session.post(f"{self.endpoint}/log", json=payload, timeout=self.timeout) 
        except Exception as e:
            print(f"[AsyncHttpSink] Failed to send event to {self.endpoint}: {e}")
