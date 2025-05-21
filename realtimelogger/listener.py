## realtimelogger/listener.py
from datetime import datetime, timezone
import json

import requests
from realtimelogger.sinks.loki import LokiSink  # Temp, later this wil be dynamic
from realtimelogger.sinks.memory import MemorySink
from realtimelogger.sinks.sqlite import SqliteSink

# from backend.memory_sink import store_event

class RealTimeLogger:
    ROBOT_LISTENER_API_VERSION = 3

    def __init__(self, config_str=None):
        config = self._parse_config(config_str)

        sink_type = config.get("sink_type", "none")
        # dashboard_enabled = config.get("dashboard_enabled", "true").lower() == "true"
        # self.dashboard_enabled = dashboard_enabled

        try:
            if sink_type == "loki":
                self.endpoint = config.get("endpoint", "http://localhost:3100")
                self.sink = LokiSink(endpoint=self.endpoint)
            elif sink_type == "memory":
                self.sink = MemorySink()
            elif sink_type == "sqlite":
                self.sink = SqliteSink()
            elif sink_type == "none":
                self.sink = None
            else:
                raise ValueError(f"Sink type '{sink_type}' wordt niet ondersteund")
        except Exception as e:
            print(f"[WARN] Sink '{sink_type}' initialisatie faalde ({e}), fallback naar MemorySink.")
            self.sink = MemorySink()

    def _send_event(self, event_type, **kwargs):
        event = {
            'event_type': event_type,
            **kwargs
            }
        
        # Push naar backend API
        try:
            requests.post("http://localhost:8000/event", json=event, timeout=0.5)
        except requests.RequestException as e:
            print(f"[WARN] Backend push faalde: {e}")
            
        if self.sink is not None:
            try:
                self.sink.handle_event(event_type, event)
            except Exception as e:
                print(f"[ERROR] Event handling failed: {e}")

    def start_test(self, name, attrs):
        self._send_event(
            "start_test",
            name=name.name,
            longname=str(attrs.longname),
            tags=[str(tag) for tag in attrs.tags],
            timestamp=str(attrs.starttime)
        )

    def end_test(self, name, attrs):
        self._send_event(
            "end_test",
            name=name.name,
            status=str(attrs.status),
            message=str(attrs.message),
            timestamp=str(attrs.endtime),
            tags=[str(tag) for tag in attrs.tags]
        )

    def _parse_config(self, config_str):
        # Simpel string parsing: ":key1=value1;key2=value2"
        config = {}
        if config_str:
            for part in config_str.split(";"):
                if "=" in part:
                    key, val = part.split("=", 1)
                    config[key.strip()] = val.strip()
        return config
    
    def _store_event(self, event):
        # Hier kan je de logica toevoegen om het event op te slaan in een centrale opslag
        # Bijvoorbeeld in een database of een bestand
        pass