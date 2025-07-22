import os
from shared.helpers.config_loader import load_config

# Detect backend type via env/config

def is_postgres():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        config = load_config()
        db_url = config.get("database_url", "")
    return db_url.startswith("postgresql")

Q = "%s" if is_postgres() else "?"
ID_FIELD = "id SERIAL PRIMARY KEY" if is_postgres() else "id INTEGER PRIMARY KEY AUTOINCREMENT"

# === RF EVENTS ===
event_columns = [
    ("event_type", "TEXT"),
    ("testid", "TEXT"),
    ("timestamp", "TEXT"),
    ("name", "TEXT"),
    ("longname", "TEXT"),
    ("suite", "TEXT"),
    ("status", "TEXT"),
    ("message", "TEXT"),
    ("elapsed", "INTEGER"),
    ("statistics", "TEXT"),
    ("tags", "TEXT"),
]

# === RF LOG MESSAGES ===
rf_log_columns = [
    ("event_type", "TEXT"),
    ("testid", "TEXT"),
    ("timestamp", "TEXT"),
    ("level", "TEXT"),
    ("message", "TEXT"),
    ("html", "TEXT"),
]



CREATE_EVENTS_TABLE = f"""
CREATE TABLE IF NOT EXISTS events (
    {ID_FIELD},
    {', '.join(f"{name} {dtype}" for name, dtype in event_columns)}
)
"""

INSERT_EVENT = f"""
INSERT INTO events ({', '.join(name for name, _ in event_columns)})
VALUES ({', '.join([Q] * len(event_columns))})
"""

SELECT_ALL_EVENTS = f"""
SELECT {', '.join(name for name, _ in event_columns)}
FROM events
ORDER BY timestamp ASC
"""

DELETE_ALL_EVENTS = "DELETE FROM events"

# === RF LOG MESSAGES ===
rf_log_columns = [
    ("event_type", "TEXT"),
    ("testid", "TEXT"),
    ("timestamp", "TEXT"),
    ("level", "TEXT"),
    ("message", "TEXT"),
    ("html", "TEXT"),
]

CREATE_RF_LOG_MESSAGE_TABLE = f"""
CREATE TABLE IF NOT EXISTS rf_log_messages (
    {ID_FIELD},
    {', '.join(f"{name} {dtype}" for name, dtype in rf_log_columns)}
)
"""

INSERT_RF_LOG_MESSAGE = f"""
INSERT INTO rf_log_messages ({', '.join(name for name, _ in rf_log_columns)})
VALUES ({', '.join([Q] * len(rf_log_columns))})
"""

SELECT_ALL_RF_LOGS = f"""
SELECT {', '.join(name for name, _ in rf_log_columns)}
FROM rf_log_messages
ORDER BY timestamp ASC
"""

# === APP LOGS ===
app_log_columns = [
    ("timestamp", "TEXT"),
    ("event_type", "TEXT"),
    ("source", "TEXT"),
    ("message", "TEXT"),
    ("level", "TEXT"),
]

CREATE_APP_LOG_TABLE = f"""
CREATE TABLE IF NOT EXISTS app_logs (
    {ID_FIELD},
    {', '.join(f"{name} {dtype}" for name, dtype in app_log_columns)}
)
"""

INSERT_APP_LOG = f"""
INSERT INTO app_logs ({', '.join(name for name, _ in app_log_columns)})
VALUES ({', '.join([Q] * len(app_log_columns))})
"""

SELECT_ALL_APP_LOGS = f"""
SELECT {', '.join(name for name, _ in app_log_columns)}
FROM app_logs
ORDER BY timestamp ASC
"""

DELETE_ALL_APP_LOGS = "DELETE FROM app_logs"

# === METRICS ===
metric_columns = [
    ("timestamp", "TEXT"),
    ("metric_name", "TEXT"),
    ("value", "REAL"),
    ("unit", "TEXT"),
    ("source", "TEXT"),
]

CREATE_METRIC_TABLE = f"""
CREATE TABLE IF NOT EXISTS metrics (
    {ID_FIELD},
    {', '.join(f"{name} {dtype}" for name, dtype in metric_columns)}
)
"""

INSERT_METRIC = f"""
INSERT INTO metrics ({', '.join(name for name, _ in metric_columns)})
VALUES ({', '.join([Q] * len(metric_columns))})
"""

SELECT_ALL_METRICS = f"""
SELECT {', '.join(name for name, _ in metric_columns)}
FROM metrics
ORDER BY timestamp ASC
"""
