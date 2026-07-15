"""FastAPI entry point for the deterministic local POC."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.app.api.demo import create_demo_router
from backend.app.api.health import router as health_router
from backend.app.api.websocket_sessions import create_websocket_router
from backend.app.orchestrator.session_manager import SessionManager

REPO_ROOT = Path(__file__).resolve().parents[2]
WEB_BUILD_DIRECTORY = REPO_ROOT / "web" / "dist"


def create_app(log_directory: Path | None = None) -> FastAPI:
    app = FastAPI(title="Emergency Training POC", version="0.1.0")
    manager = SessionManager(log_directory) if log_directory is not None else SessionManager()
    app.state.session_manager = manager
    app.include_router(health_router)
    app.include_router(create_demo_router(manager))
    app.include_router(create_websocket_router(manager))
    if WEB_BUILD_DIRECTORY.is_dir():
        app.mount("/", StaticFiles(directory=WEB_BUILD_DIRECTORY, html=True), name="demo-web")
    return app


app = create_app()
