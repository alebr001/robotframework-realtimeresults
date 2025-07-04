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
"""

DELETE_ALL_EVENTS = "DELETE FROM events"

#############

CREATE_RF_LOG_MESSAGE_TABLE = """
CREATE TABLE IF NOT EXISTS rf_log_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    testid TEXT,
    timestamp TEXT,
    level TEXT,
    message TEXT,
    html BOOLEAN
);
"""

INSERT_RF_LOG_MESSAGE = """
INSERT INTO rf_log_messages (testid, timestamp, level, message, html)
VALUES (?, ?, ?, ?, ?);
"""

##############

CREATE_APP_LOG_TABLE = """
CREATE TABLE IF NOT EXISTS app_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    event_type TEXT,
    source TEXT,
    message TEXT,
    level TEXT
)
"""

INSERT_APP_LOG = """
INSERT INTO app_logs (timestamp, event_type, source, message, level)
VALUES (?, ?, ?, ?, ?)
"""

SELECT_ALL_APP_LOGS = """
    SELECT timestamp, event_type, source, message, level
    FROM app_logs
    ORDER BY timestamp ASC
"""

##############


CREATE_METRIC_TABLE = """
CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    name TEXT,
    value REAL,
    unit TEXT
)
"""

INSERT_METRIC = """
INSERT INTO metrics (timestamp, name, value, unit)
VALUES (?, ?, ?, ?)
"""
