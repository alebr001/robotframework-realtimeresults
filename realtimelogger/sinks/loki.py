import requests
from .base import EventSink

class LokiSink(EventSink):
    def __init__(self, endpoint):
        super().__init__()
        self.endpoint = endpoint.rstrip('/') + '/loki/api/v1/push'

    def _handle_event(self, data):
        log_entry = {
            "streams": [{
                "labels": '{job=\"robotframework\",event=\"%s\"}' % data.get('event_type'),
                "entries": [{
                    "ts": data.get('timestamp'),
                    "line": str(data)
                }]
            }]
        }
        response = requests.post(self.endpoint, json=log_entry)
        response.raise_for_status()
