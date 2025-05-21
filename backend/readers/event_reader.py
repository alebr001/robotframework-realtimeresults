# backend/event_reader.py

class EventReader:
    def get_events(self) -> list[dict]:
        raise NotImplementedError
    
    def clear_events(self) -> None:
        raise NotImplementedError