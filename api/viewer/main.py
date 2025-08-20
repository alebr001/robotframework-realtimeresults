from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from shared.helpers.config_loader import load_config
from shared.helpers.ensure_db_schema import ensure_schema
from shared.helpers.logger import setup_root_logging
from api.viewer.readers.sqlite_reader import SqliteReader
from api.viewer.readers.postgres_reader import PostgresReader
from api.viewer.event_manager import EventManager
from shared.middleware.tenant_middleware import TenantMiddleware
from api.viewer import routes as viewer_routes
from fastapi.middleware.cors import CORSMiddleware

config = load_config()
# Ensure database schema is up-to-date
ensure_schema(config.get("database_url", "sqlite:///eventlog.db"))
setup_root_logging(config.get("log_level", "info"))
logger = logging.getLogger("rt.api.viewer")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Viewer API started successfully")
    logger.info("Dashboard available at: /dashboard")
    yield
    logger.info("Shutting down Viewer API")


app = FastAPI(lifespan=lifespan)

ALLOWED_ORIGINS = [
    "http://127.0.0.1:8002",
    "http://localhost:8002",
]

TEST_ORIGINS = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=TEST_ORIGINS,   # of ["*"] tijdens lokaal testen
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.add_middleware(TenantMiddleware)

# Routing
app.include_router(viewer_routes.router)
app.mount("/dashboard", StaticFiles(directory="dashboard", html=True), name="dashboard")

# Readers
database_url = config.get("database_url", "sqlite:///eventlog.db")
if database_url.startswith("sqlite:///"):
    event_reader = SqliteReader(database_url=database_url)
elif database_url.startswith(("postgresql://", "postgres://")):
    event_reader = PostgresReader(database_url=database_url)
else:
    raise ValueError("Unsupported databasetype")

app.state.event_reader = event_reader
app.state.event_manager = EventManager()

