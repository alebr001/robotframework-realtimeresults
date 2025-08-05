## realtimeresults/listener.py
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

def generate_test_id(data, result) -> str:
    """Generate a unique test ID based on longname and starttime."""
    return f"{data.longname}::{to_iso_utc(result.starttime)}"

class RealTimeResults:
    ROBOT_LISTENER_API_VERSION = 3

    def __init__(self, config_str=None):
        self.logger = logging.getLogger("rt.lstnr")
        component_level_logging = config.get("log_level_listener")
        if component_level_logging:
            self.logger.setLevel(getattr(logging, component_level_logging.upper(), logging.INFO))

        self.logger.debug("----------------")
        self.logger.debug("Started listener")
        self.logger.debug("----------------")

        file_config = load_config()  # {"sink_type": "sqlite", "debug": false}
        cli_config = self._parse_config(config_str)
        self.config = {**file_config, **cli_config}

        self.listener_sink_type = self.config.get("listener_sink_type", "none").lower()
        self.total_tests = int(cli_config.get("totaltests", 0))
        self.current_test_id = None
        endpoint = ""
        try:
            if self.listener_sink_type == "http":
                host = self.config.get("ingest_backend_host", "127.0.0.1")
                port = self.config.get("ingest_backend_port", "8001")
                endpoint = f"http://{host}:{port}"
                self.sink = HttpSink(endpoint=endpoint)

            elif self.listener_sink_type == "sqlite":
                database_url = self.config.get("database_url", "none")
                if database_url.startswith("sqlite:///"):
                    self.sink = SqliteSink(database_url=database_url)
                else:
                    raise ValueError(f"Unsupported database_url for sync: {database_url}")

            elif self.listener_sink_type == "loki":
                endpoint = self.config.get("loki_endpoint", "http://localhost:3100")
                self.sink = LokiSink(endpoint=endpoint)

            elif self.listener_sink_type == "none":
                self.sink = None
            else:
                raise ValueError(f"Unsupported sink_type: {self.listener_sink_type}, options are: http, sqlite, loki, none")
        except Exception as e:
            self.logger.warning(f"[Sink initialisatie failed ({e}), no sink selected.")
            self.sink = None

    def _send_event(self, event_type, **kwargs):
        event = {
            "event_type": event_type,
            **kwargs
            }
         
        # Push to sink
        if self.sink is not None:
            try:
                self.sink.handle_event(event) 
            except Exception as e:
                self.logger.error(f"Event handling failed: {e}")
        else:
            self.logger.debug(f"[DEBUG] No sink configured for sink_type='{self.listener_sink_type}' — event ignored.")

    def log_message(self, message):
        self._send_event(
            "log_message",
            testid=self.current_test_id,
            timestamp=to_iso_utc(message.timestamp),
            level=message.level,
            message=message.message,
            html=message.html,
        )

    def start_test(self, data, result):
        self.current_test_id = generate_test_id(data, result)
        self._send_event(
            "start_test",
            testid=self.current_test_id,
            starttime=to_iso_utc(result.starttime),
            endtime=to_iso_utc(result.endtime),
            name=data.name,
            longname=data.longname,
            suite=data.longname.split('.')[0],
            tags=[str(tag) for tag in data.tags]
        )

    def end_test(self, data, result):
        self._send_event(
            "end_test",
            testid=self.current_test_id,
            starttime=to_iso_utc(result.starttime),
            endtime=to_iso_utc(result.endtime),
            name=data.name,
            longname=data.longname,
            suite = ".".join(data.longname.split(".")[:-1]),
            status=str(result.status),
            message=str(result.message),
            elapsed = result.elapsedtime / 1000 if hasattr(data, "elapsedtime") else None,
            tags=[str(tag) for tag in data.tags]
        )
        self.current_test_id = None

    def start_suite(self, data, result):
        self._send_event(
            "start_suite",
            starttime=to_iso_utc(result.starttime),
            endtime=to_iso_utc(result.endtime),
            name=data.name,
            longname=data.longname,
            totaltests=self.total_tests
        )

    def end_suite(self, data, result):
        self._send_event(
            "end_suite",
            starttime=to_iso_utc(result.starttime),
            endtime=to_iso_utc(result.endtime),
            name=data.name,
            longname=data.longname,
            status=result.status,
            message=result.message,
            elapsed=result.elapsedtime / 1000,
            statistics=str(result.statistics)
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
    

