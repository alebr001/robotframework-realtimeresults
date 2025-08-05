## realtimeresults/sinks/base.py
from abc import ABC, abstractmethod
import json
import logging

class BaseIngestSink(ABC):
    """
    Base class for asynchronous event sinks.

    Subclasses must implement async event handlers that accept a single `data` dictionary.
    Each handler is responsible for managing its own database connection and committing changes.

    Do NOT assume the dispatcher will pass in a connection object.
    This decouples the dispatcher logic from specific database implementations and promotes modularity.

    Example signature:
        async def _handle_app_log(self, data: dict) -> None
    """

    def __init__(self):
        self.logger = logging.getLogger("rt.sink")

    @abstractmethod
    async def initialize_database(self):
        """Must be implemented by async sinks."""
        pass     
    
    @abstractmethod
    async def handle_app_log(self, data):
        """Must be implemented by async sinks."""
        pass

    @abstractmethod
    async def handle_metric(self, data):
        """Must be implemented by async sinks."""
        pass

    @abstractmethod
    async def handle_rf_events(self, data):
        """Must be implemented by async sinks."""
        pass

    @abstractmethod
    async def handle_rf_log(self, data):
        """Must be implemented by async sinks."""
        pass
    
    @staticmethod
    def make_sql_safe(value):
        """Convert non-string types to JSON strings for safe DB insertion."""
        if value is None:
            return None
        if isinstance(value, (list, dict, bool)):
            return json.dumps(value)
        return value