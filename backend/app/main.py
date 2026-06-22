"""FastAPI entry point for the deterministic local POC."""

from pathlib import Path

from fastapi import FastAPI

from backend.app.api.health import router as health_router
from backend.app.api.websocket_sessions import create_websocket_router
from backend.app.orchestrator.session_manager import SessionManager


def create_app(log_directory: Path | None = None) -> FastAPI:
    app = FastAPI(title="Emergency Training POC", version="0.1.0")
    manager = SessionManager(log_directory) if log_directory is not None else SessionManager()
    app.state.session_manager = manager
    app.include_router(health_router)
    app.include_router(create_websocket_router(manager))
    return app


app = create_app()
