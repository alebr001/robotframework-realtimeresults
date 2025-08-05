# api/viewer/app_factory.py
from fastapi import FastAPI
from shared.helpers.ensure_db_schema import ensure_schema
from api.viewer.routes import router as viewer_routes

def create_app(config: dict) -> FastAPI:
    app = FastAPI()
    app.include_router(viewer_routes)
    return app
