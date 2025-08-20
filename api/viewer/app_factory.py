import logging
from fastapi import FastAPI, Path
from fastapi.concurrency import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from api.viewer.routes import router as viewer_routes
from api.viewer.event_manager import EventManager
from fastapi.middleware.cors import CORSMiddleware
from importlib import resources

from shared.helpers.ensure_db_schema import ensure_schema
from shared.helpers.logger import setup_root_logging
from api.viewer.readers.sqlite_reader import SqliteReader
from api.viewer.readers.postgres_reader import PostgresReader
from api.viewer.event_manager import EventManager
from api.viewer import routes as viewer_routes
from shared.middleware.tenant_middleware import TenantMiddleware



ALLOWED_ORIGINS = "*"

def _mount_dashboard(app: FastAPI) -> None:
    """
    Mount the dashboard in a cross‑platform way.
    Prefer a packaged resource; fall back to local 'dashboard' folder during development.
    """
    # Try packaged dashboard (if included as a package/module resource)
    try:
        # Example if you package dashboard as a module with static assets
        pkg_root = resources.files("dashboard")  # requires dashboard to be a package
        app.mount("/dashboard", StaticFiles(directory=str(pkg_root), html=True), name="dashboard")
        return
    except Exception:
        pass

    # Fallback to local folder for dev installs
    local_dir = Path("dashboard")
    if local_dir.exists():
        app.mount("/dashboard", StaticFiles(directory=str(local_dir), html=True), name="dashboard")

def _build_event_reader(database_url: str):
    """Return the appropriate reader instance based on DB URL."""
    if database_url.startswith("sqlite:///"):
        return SqliteReader(database_url=database_url)
    if database_url.startswith(("postgresql://", "postgres://")):
        return PostgresReader(database_url=database_url)
    raise ValueError("Unsupported databasetype")

def create_app(config: dict) -> FastAPI:
    """
    App factory for the viewer API.
    All side effects (logging, DB schema, mounts) are performed here, not at import time.
    """
    # Logging setup first so subsequent steps log cleanly
    setup_root_logging(config.get("log_level", "info"))
    logger = logging.getLogger("rt.api.viewer")

    # Ensure schema is idempotent and safe to call on startup
    database_url = config.get("database_url", "sqlite:///eventlog.db")
    ensure_schema(database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("Viewer API started successfully")
        logger.info("Dashboard available at: /dashboard")
        yield
        logger.info("Shutting down Viewer API")

    app = FastAPI(lifespan=lifespan)

    # CORS (allow * for local/test; restrict in prod through config)
    if(config.get("ingest_client_host")):
        url = config.get("ingest_viewer_host", "127.0.0.1") + ":" + str(config.get("ingest_viewer_port", "8002"))
        allow_origins = [url] 
    else:
        allow_origins = ALLOWED_ORIGINS


    allow_origins = [str(config.get("ingest_client_host")":")] or ALLOWED_ORIGINS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # Multitenancy
    app.add_middleware(TenantMiddleware)

    # Routes
    app.include_router(viewer_routes.router)

    # Static dashboard
    _mount_dashboard(app)

    # Readers + event manager in app state
    app.state.event_reader = _build_event_reader(database_url)
    app.state.event_manager = EventManager()
    app.state.config = config

    return app