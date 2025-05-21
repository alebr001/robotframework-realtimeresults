## realtimelogger/sinks/base.py
class EventSink:
    def handle_event(self, event_type: str, data: dict):
        raise NotImplementedError("Subclasses have to implement handle_event")