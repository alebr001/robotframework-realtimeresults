# realtimelogger/sinks/http.py

import requests

class HttpSink:
    def __init__(self, endpoint="http://localhost:8000/event", timeout=0.5):
        self.endpoint = endpoint
        self.timeout = timeout

    def handle_event(self, event_type, data):
        payload = dict(data)  # shallow copy
        payload["event_type"] = event_type
        try:
            requests.post(self.endpoint, json=payload, timeout=self.timeout)
        except requests.RequestException as e:
            print(f"[WARN] Failed to post event to {self.endpoint}: {e}")