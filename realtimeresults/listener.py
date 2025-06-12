## realtimeresults/listener.py
import requests
from helpers.config_loader import load_config
from realtimeresults.sinks.http import HttpSink
from realtimeresults.sinks.loki import LokiSink
from realtimeresults.sinks.sqlite import SqliteSink
from helpers.logger import setup_logging
import logging

logger = logging.getLogger(__name__)
config = load_config()
setup_logging(config.get("log_level_listener", "warn"))

class RealTimeResults:
    ROBOT_LISTENER_API_VERSION = 3

    def __init__(self, config_str=None):

        logger.info("----------------")
        logger.info("Started listener")
        logger.info("----------------")

        file_config = load_config()  # {"sink_type": "sqlite", "debug": false}
        cli_config = self._parse_config(config_str)
        self.config = {**file_config, **cli_config}

        self.sink_type = self.config.get("sink_type", "none").lower()
        # self.debug = self.config.get("debug", "false") == "true"

        strategy = self.config.get("sink_strategy", "local")
        try:
            if strategy == "http":
                if self.sink_type == "loki":
                    self.endpoint = self.config.get("endpoint", "http://localhost:3100")
                    self.sink = LokiSink(endpoint=self.endpoint)
                elif self.sink_type == "sqlite":
                    self.sink = HttpSink(endpoint=self.config.get("endpoint", "http://localhost:8000/event"))
                else:
                    raise ValueError(f"Unsupported sink_type: {self.sink_type}")
            elif strategy == "local":
                if self.sink_type == "sqlite":
                    self.sink = SqliteSink(database_path=self.config.get("database_path", "eventlog.db"))
                elif self.sink_type == "none":
                    self.sink = None
                else:
                    raise ValueError(f"Unsupported sink_type: {self.sink_type}")
            else:
                raise ValueError(f"Unsupported sink strategy '{strategy}'")
        except Exception as e:
            logger.warning(f"[WARN] Sink '{self.sink_type}' initialisatie failed ({e}), no sink selected.")
            self.sink = None

    def _send_event(self, event_type, **kwargs):
        event = {
            "event_type": event_type,
            **kwargs
            }
         
        # Push naar backend API
        if self.sink_type == "memory":
            try:
                requests.post("http://localhost:8000/event", json=event, timeout=0.5)
            except requests.RequestException as e:
                logger.warning(f"[WARN] Backend push faalde: {e}")
        elif self.sink is not None:
            try:
                self.sink.handle_event(event) 
            except Exception as e:
                logger.error(f"[ERROR] Event handling failed: {e}")
        else:
            logger.debug(f"[DEBUG] No sink configured for sink_type='{self.sink_type}' — event ignored.")

    def start_test(self, name, attrs):
        test_id = f"{attrs.longname}::{attrs.starttime}"
        self._send_event(
            "start_test",
            testid=test_id,
            name=attrs.name,
            longname=attrs.longname,
            suite=attrs.longname.split('.')[0],
            tags=attrs.tags,
            timestamp=attrs.starttime
        )

    def end_test(self, name, attrs):
        test_id = f"{attrs.longname}::{attrs.starttime}"
        self._send_event(
            "end_test",
            testid=test_id,
            name=name.name,
            suite = ".".join(attrs.longname.split(".")[:-1]),
            status=str(attrs.status),
            message=str(attrs.message),
            elapsed = attrs.elapsedtime / 1000 if hasattr(attrs, "elapsedtime") else None,
            timestamp=str(attrs.endtime),
            tags=[str(tag) for tag in attrs.tags]
        )

    def start_suite(self, name, attrs):
        self._send_event(
            "start_suite",
            name=attrs.name,
            longname=attrs.longname,
            timestamp=attrs.starttime,
            totaltests=len(attrs.tests)
        )

    def end_suite(self, name, attrs):
        self._send_event(
            "end_suite",
            name=attrs.name,
            longname=attrs.longname,
            timestamp=attrs.endtime,
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
