# backend/event_reader.py

from abc import abstractmethod
from typing import List, Dict
import logging


class EventReader:
    def __init__(self, database_path=None):
        self.logger = logging.getLogger(self.__class__.__module__)

    def get_events(self):
        self.logger.debug("Fetching events using %s", self.__class__.__name__)
        return self._get_events()   
    
    def clear_events(self):
        self.logger.debug("Clearing events using %s", self.__class__.__name__)
        return self._clear_events()
        
    @abstractmethod
    def _get_events(self) -> List[Dict]:
        pass

    @abstractmethod
    def _clear_events(self) -> None:
        pass
