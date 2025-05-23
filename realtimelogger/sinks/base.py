## realtimelogger/sinks/base.py
from abc import abstractmethod
import logging

class EventSink:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__module__)

    def handle_event(self, data):
        self.logger.debug("[%s] Handling event for %s", self.__class__.__name__,  data.get("event_type"))
        self._handle_event(data)

    @abstractmethod
    def _handle_event(self, data):
        pass