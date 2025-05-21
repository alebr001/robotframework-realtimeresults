## realtimelogger/listener.py
from realtimelogger.sinks.loki import LokiSink  # Temp, later this wil be dynamic
from datetime import datetime

class RealTimeLogger:
    ROBOT_LISTENER_API_VERSION = 3

    def __init__(self, sink_type='loki', sink_config_str=None):
        # Simpel string parsing: "key1=value1;key2=value2"
        config = {}
        if sink_config_str:
            for part in sink_config_str.split(';'):
                k, v = part.split('=')
                config[k.strip()] = v.strip()

        if sink_type == 'loki':
            self.sink = LokiSink(**config)
        else:
            raise ValueError(f"Sink type '{sink_type}' wordt niet ondersteund")

    def _send_event(self, event_type, **kwargs):
        data = {
            'event': event_type,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            **kwargs
        }
        self.sink.handle_event(event_type, data)

    def start_test(self, name, attrs):
        self._send_event('start_test', name=name, tags=attrs.get('tags', []))

    def end_test(self, name, attrs):
        self._send_event('end_test', name=name, status=attrs.get('status'))
