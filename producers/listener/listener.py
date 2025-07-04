## realtimeresults/listener.py
import requests
import logging
from shared.helpers.config_loader import load_config
from shared.helpers.logger import setup_root_logging
from shared.sinks.http import HttpSink
from shared.sinks.loki import LokiSink
from shared.sinks.sqlite import SqliteSink
from datetime import datetime, timezone

config = load_config()
setup_root_logging(config.get("log_level", "info"))


def to_iso_utc(timestr) -> str:
    """Convert RF-style timestamp to ISO 8601 with UTC timezone."""
    if isinstance(timestr, datetime):
        return timestr.astimezone(timezone.utc).isoformat()
    if isinstance(timestr, str):
        # Robot Framework timestamp: "20250620 22:03:27.788524"
        try:
            dt = datetime.strptime(timestr, "%Y%m%d %H:%M:%S.%f")
        except ValueError:
            # Fall back to default datetime string format (rare gevallen)
            dt = datetime.fromisoformat(timestr)
        return dt.astimezone(timezone.utc).isoformat()
    raise TypeError(f"Unsupported type for to_iso_utc: {type(timestr)}")

def generate_test_id(attrs) -> str:
    """Generate a unique test ID based on longname and starttime."""
    return f"{attrs.longname}::{to_iso_utc(attrs.starttime)}"

class RealTimeResults:
    ROBOT_LISTENER_API_VERSION = 3

    def __init__(self, config_str=None):
        self.logger = logging.getLogger("rt.lstnr")
        component_level_logging = config.get("log_level_listener")
        if component_level_logging:
            self.logger.setLevel(getattr(logging, component_level_logging.upper(), logging.INFO))

        self.logger.info("----------------")
        self.logger.info("Started listener")
        self.logger.info("----------------")
        self.logger.debug("------DEBUGTEST----------")

        file_config = load_config()  # {"sink_type": "sqlite", "debug": false}
        cli_config = self._parse_config(config_str)
        self.config = {**file_config, **cli_config}

        self.listener_sink_type = self.config.get("listener_sink_type", "none").lower()
        self.total_tests = int(cli_config.get("totaltests", 0))
        self.current_test_id = None
        
        try:
            if self.listener_sink_type == "backend_http_inmemory":
                self.sink = HttpSink(endpoint=self.config.get("backend_endpoint", "http://localhost:8000"))
            elif self.listener_sink_type == "loki":
                self.endpoint = self.config.get("loki_endpoint", "http://localhost:3100")
                self.sink = LokiSink(endpoint=self.endpoint)
            elif self.listener_sink_type == "sqlite":
                self.sink = SqliteSink(database_path=self.config.get("database_path", "eventlog.db"))
            elif self.listener_sink_type == "none":
                self.sink = None
            else:
                raise ValueError(f"Unsupported sink_type: {self.listener_sink_type}")

        except Exception as e:
            self.logger.warning(f"[WARN] Sink '{self.listener_sink_type}' initialisatie failed ({e}), no sink selected.")
            self.sink = None

    def _send_event(self, event_type, **kwargs):
        event = {
            "event_type": event_type,
            **kwargs
            }
         
        # Push naar backend API
        if self.listener_sink_type == "backend_http_inmemory":
            try:
                requests.post("http://localhost:8000/event", json=event, timeout=0.5)
            except requests.RequestException as e:
                self.logger.warning(f"[WARN] Backend push faalde: {e}")
        elif self.sink is not None:
            try:
                self.sink.handle_event(event) 
            except Exception as e:
                self.logger.error(f"[ERROR] Event handling failed: {e}")
        else:
            self.logger.debug(f"[DEBUG] No sink configured for sink_type='{self.listener_sink_type}' — event ignored.")

    def log_message(self, message):
        self._send_event(
            "log_message",
            message=message.message,
            testid=self.current_test_id,
            level=message.level,
            timestamp=to_iso_utc(message.timestamp),
            html=message.html,
        )

    def start_test(self, name, attrs):
        self.current_test_id = generate_test_id(attrs)
        self._send_event(
            "start_test",
            testid=self.current_test_id,
            name=attrs.name,
            longname=attrs.longname,
            suite=attrs.longname.split('.')[0],
            tags=attrs.tags,
            timestamp=to_iso_utc(attrs.starttime)
        )

    def end_test(self, name, attrs):
        self._send_event(
            "end_test",
            testid=self.current_test_id,
            name=name.name,
            suite = ".".join(attrs.longname.split(".")[:-1]),
            status=str(attrs.status),
            message=str(attrs.message),
            elapsed = attrs.elapsedtime / 1000 if hasattr(attrs, "elapsedtime") else None,
            timestamp=to_iso_utc(attrs.endtime),
            tags=[str(tag) for tag in attrs.tags]
        )
        self.current_test_id = None

    def start_suite(self, name, attrs):
        self._send_event(
            "start_suite",
            name=attrs.name,
            longname=attrs.longname,
            timestamp=to_iso_utc(attrs.starttime),
            totaltests=self.total_tests
        )

    def end_suite(self, name, attrs):
        self._send_event(
            "end_suite",
            name=attrs.name,
            longname=attrs.longname,
            timestamp=to_iso_utc(attrs.endtime),
            elapsed=attrs.elapsedtime / 1000,
            status=attrs.status,
            message=attrs.message,
            statistics=str(attrs.statistics)
        )

    def _parse_config(self, config_str):
        # Simple string parsing: ":key1=value1;key2=value2"
        config = {}
        if config_str:
            for part in config_str.split(";"):
                if "=" in part:
                    key, val = part.split("=", 1)
                    config[key.strip()] = val.strip()
        return config
    

