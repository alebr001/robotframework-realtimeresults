# api/viewer/app_factory.py
from fastapi import FastAPI
from shared.helpers.ensure_db_schema import ensure_schema
from api.viewer.routes import router as viewer_routes
from fastapi.middleware.cors import CORSMiddleware

def create_app(config: dict) -> FastAPI:
    app = FastAPI()
    # TODO use config to only allow cross origin from dashboard API
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(viewer_routes)
    return app

