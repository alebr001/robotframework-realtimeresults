import sqlite3
from helpers.sql_definitions import CREATE_EVENTS_TABLE, INSERT_EVENT

class MemorySqliteSink:
    def __init__(self):
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self._initialize()

    def _initialize(self):
        cursor = self.conn.cursor()
        cursor.execute(CREATE_EVENTS_TABLE)
        self.conn.commit()

    def get_connection(self):
        """
        Expose connection for user in SqliteEventReader.
        """
        return self.conn
    
    def handle_event(self, data):
        tags = data.get("tags", [])
        if not isinstance(tags, list):
            try:
                tags = list(tags)
            except Exception:
                tags = [str(tags)]

        tag_string = ",".join(str(tag) for tag in tags)


        cursor = self.conn.cursor()
        cursor.execute(INSERT_EVENT, (
            data.get("testid"),
            data.get("timestamp"),
            data.get("event_type"),
            str(data.get("name")),
            str(data.get("suite")),
            data.get("status"),
            data.get("message"),
            data.get("elapsed"),
            tag_string
            ))
        self.conn.commit()
