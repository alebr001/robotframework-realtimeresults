# backend/event_reader.py

from abc import ABC, abstractmethod
from typing import List, Dict
import logging


class Reader(ABC):
    def __init__(self, database_url=None):
        self.logger = logging.getLogger(self.__class__.__module__)

    def get_events(self):
        self.logger.debug("Fetching events using %s", self.__class__.__name__)
        return self._get_events()
    
    def get_app_logs(self):
        self.logger.debug("Clearing events using %s", self.__class__.__name__)
        return self._get_app_logs()
    
    def clear_events(self):
        self.logger.debug("Clearing events using %s", self.__class__.__name__)
        return self._clear_events()

    @abstractmethod
    def _get_events(self) -> List[Dict]:
        """Internal method implemented by subclass"""
        pass

    @abstractmethod
    def _get_app_logs(self) -> List[Dict]:
        """Internal method implemented by subclass"""
        pass

    @abstractmethod
    def _clear_events(self) -> None:
        """Internal method implemented by subclass"""
        pass
