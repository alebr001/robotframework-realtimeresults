import logging
import sqlite3
import sys
from fastapi import Request
from fastapi.responses import JSONResponse

from api.ingest.app_factory import create_app

logger = logging.getLogger("rt.api.ingest")

try:
    app = create_app()
except Exception as e:
    logger.error("Failed to start ingest API.", exc_info=e)
    sys.exit(1)

@app.exception_handler(sqlite3.OperationalError)
async def sqlite_error_handler(request: Request, exc: sqlite3.OperationalError):
    logger.warning("Database unavailable during request to %s: %s", request.url.path, str(exc))
    return JSONResponse(
        status_code=503,
        content={"detail": f"Database error: {str(exc)}"}
    )
