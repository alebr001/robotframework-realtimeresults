## realtimeresults/sinks/base.py
from abc import ABC, abstractmethod
import logging

class EventSink(ABC):
    """
    Base class for synchronous event sinks.

    Subclasses must implement event handlers that accept a database connection
    object and a `data` dictionary. The connection is created and passed in
    by the dispatcher, which is responsible for managing transaction scope.

    This pattern allows multiple event types to be processed within the same
    database session, reducing overhead and improving consistency.

    Example signature:
        def _handle_app_log(self, conn, data: dict) -> None

    Note:
        This differs from AsyncEventSink, where each handler must open its own
        connection and manage its own transaction.
    """
    
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