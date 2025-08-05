import sqlite3
import logging
import sys

from shared.helpers.config_loader import load_config
from shared.helpers.ensure_db_schema import ensure_schema
from shared.helpers.logger import setup_root_logging

from api.viewer.readers.sqlite_reader import SqliteReader
from api.viewer.readers.postgres_reader import PostgresReader
from api.viewer.app_factory import create_app

from fastapi import Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime, timezone

from api.viewer.app_factory import create_app

config = load_config()
ensure_schema(config.get("database_url", "sqlite:///eventlog.db"))
setup_root_logging(config.get("log_level", "info"))
logger = logging.getLogger("rt.api.viewer")

component_level_logging = config.get("log_level_cli")
if component_level_logging:
    logger.setLevel(getattr(logging, component_level_logging.upper(), logging.INFO))

logger.debug("Starting FastAPI application")

try:
    app = create_app(config)
except Exception as e:
    logger.error("Failed to start viewer API.", exc_info=e)
    sys.exit(1)

app.mount("/dashboard", StaticFiles(directory="dashboard", html=True), name="dashboard")

database_url = config.get("database_url", "sqlite:///eventlog.db")

if database_url.startswith("sqlite:///"):
    event_reader = SqliteReader(database_url=database_url)
elif database_url.startswith(("postgresql://", "postgres://")):
    event_reader = PostgresReader(database_url=database_url)
else:
    raise ValueError("Unsupported databasetype")

# Expose reader to routes
app.state.event_reader = event_reader

@app.exception_handler(sqlite3.OperationalError)
async def sqlite_error_handler(request: Request, exc: sqlite3.OperationalError):
    logger.warning("Database unavailable during request to %s: %s", request.url.path, str(exc))
    return JSONResponse(
        status_code=503,
        content={"detail": f"Database error: {str(exc)}"}
    )