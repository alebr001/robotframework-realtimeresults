## realtimeresults/sinks/base.py
from abc import ABC, abstractmethod
import logging

from shared.helpers.config_loader import load_config

class EventSink(ABC):
    """Base class for synchronous sinks."""

    def __init__(self):
        self.logger = logging.getLogger("rt.sink")

    def handle_event(self, data):
        """Public entry point for synchronous sinks."""
        self.logger.debug("[%s] Handling event: %s", self.__class__.__name__, data.get("event_type"))
        self._handle_event(data)

    @abstractmethod
    def _handle_event(self, data):
        """Must be implemented by sync sinks."""
        pass


class AsyncEventSink(ABC):
    """Base class for asynchronous sinks."""

    def __init__(self):
        # config = load_config()
        self.logger = logging.getLogger("rt.sink")

    async def async_handle_event(self, data):
        """Public entry point for async sinks."""
        self.logger.debug("[%s] Handling async event: %s", self.__class__.__name__, data.get("event_type"))
        await self._async_handle_event(data)

    @abstractmethod
    async def _async_handle_event(self, data):
        """Must be implemented by async sinks."""
        pass        