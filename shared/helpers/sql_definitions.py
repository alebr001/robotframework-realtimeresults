# sql_definitions.py
# This module defines SQL statements and column definitions for multiple database types.
# It supports both SQLite (using '?') and PostgreSQL (using '$1', '$2', etc.).

import os
from shared.helpers.config_loader import load_config

# Determine whether PostgreSQL is used based on config or environment variable
def is_postgres():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        config = load_config()
        db_url = config.get("database_url", "")
    return db_url.startswith("postgresql")

# Generate correct SQL placeholder syntax
# PostgreSQL requires $1, $2, ... while SQLite uses ?
def placeholder(index: int) -> str:
    return f"${index}" if is_postgres() else "?"

# Generate comma-separated placeholders for given number of columns
# SQLite example: ?, ?, ?
# PostgreSQL example: $1, $2, $3,
def placeholders(n: int) -> str:
    return ", ".join([placeholder(i + 1) for i in range(n)])

# Define ID column depending on backend
ID_FIELD = "id SERIAL PRIMARY KEY" if is_postgres() else "id INTEGER PRIMARY KEY AUTOINCREMENT"

# === Robot Framework Events Table ===
event_columns = [
    ("event_type", "TEXT"),
    ("testid", "TEXT"),
    ("starttime", "TEXT"),
    ("endtime", "TEXT"),
    ("name", "TEXT"),
    ("longname", "TEXT"),
    ("suite", "TEXT"),
    ("status", "TEXT"),
    ("message", "TEXT"),
    ("elapsed", "INTEGER"),
    ("statistics", "TEXT"),
    ("tags", "TEXT"),
]

CREATE_EVENTS_TABLE = f"""
CREATE TABLE IF NOT EXISTS events (
    {ID_FIELD},
    {', '.join(f"{name} {dtype}" for name, dtype in event_columns)}
)
"""

INSERT_EVENT = f"""
INSERT INTO events ({', '.join(name for name, _ in event_columns)})
VALUES ({placeholders(len(event_columns))})
"""

SELECT_ALL_EVENTS = f"""
SELECT {', '.join(name for name, _ in event_columns)}
FROM events
ORDER BY COALESCE(starttime, endtime) ASC
"""

DELETE_ALL_EVENTS = "DELETE FROM events"

# === RF Log Messages Table ===
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
VALUES ({placeholders(len(rf_log_columns))})
"""

SELECT_ALL_RF_LOGS = f"""
SELECT {', '.join(name for name, _ in rf_log_columns)}
FROM rf_log_messages
ORDER BY timestamp ASC
"""

# === Application Logs Table ===
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
VALUES ({placeholders(len(app_log_columns))})
"""

SELECT_ALL_APP_LOGS = f"""
SELECT {', '.join(name for name, _ in app_log_columns)}
FROM app_logs
ORDER BY timestamp ASC
"""

DELETE_ALL_APP_LOGS = "DELETE FROM app_logs"

# === Metrics Table ===
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
VALUES ({placeholders(len(metric_columns))})
"""

SELECT_ALL_METRICS = f"""
SELECT {', '.join(name for name, _ in metric_columns)}
FROM metrics
ORDER BY timestamp ASC
"""
