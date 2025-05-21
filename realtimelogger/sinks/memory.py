from .base import EventSink

class MemorySink(EventSink):
    def __init__(self):
        self.events = []

    def handle_event(self, event_type, data):
        self.events.append({"type": event_type, "data": data})