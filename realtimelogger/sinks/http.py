# realtimelogger/sinks/http.py
import requests
from .base import EventSink

class HttpSink(EventSink):
    def __init__(self, endpoint="http://localhost:8000/event", timeout=0.5):
        super().__init__()
        self.endpoint = endpoint
        self.timeout = timeout

    def _handle_event(self, data):
        payload = dict(data)  # shallow copy
        try:
            requests.post(self.endpoint, json=payload, timeout=self.timeout)
        except requests.RequestException as e:
            print(f"[WARN] Failed to post event to {self.endpoint}: {e}")