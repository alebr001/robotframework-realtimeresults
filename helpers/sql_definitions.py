CREATE_EVENTS_TABLE = """
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        testid TEXT,
        timestamp TEXT,
        event_type TEXT,
        name TEXT,
        suite TEXT,
        status TEXT,
        message TEXT,
        elapsed INTEGER,
        tags TEXT
    )
"""

INSERT_EVENT = """
    INSERT INTO events (
        testid,
        timestamp,
        event_type,
        name,
        suite,
        status,
        message,
        elapsed,
        tags
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

SELECT_ALL_EVENTS = """
    SELECT timestamp, event_type, name, suite, status, message, elapsed, tags
    FROM events
    ORDER BY timestamp ASC
    LIMIT 100
"""

DELETE_ALL_EVENTS = "DELETE FROM events"