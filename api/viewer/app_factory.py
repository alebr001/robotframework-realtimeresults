from fastapi import FastAPI
from shared.helpers.ensure_db_schema import ensure_schema
from api.viewer.routes import router as viewer_routes
from api.viewer.event_manager import EventManager

def create_app(config: dict) -> FastAPI:
    app = FastAPI()
    
    # Create and attach event manager
    app.state.event_manager = EventManager()
    
    app.include_router(viewer_routes)
    return app