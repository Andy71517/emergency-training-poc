"""Small HTTP boundary for the local presentation webpage."""

from fastapi import APIRouter, HTTPException

from backend.app.demo_catalog import DEMO_DEFINITIONS
from backend.app.logging.review_summary import generate_review_summary
from backend.app.orchestrator.session_manager import SessionManager
from backend.app.security import ensure_safe_identifier


def create_demo_router(session_manager: SessionManager) -> APIRouter:
    router = APIRouter(prefix="/api/demo", tags=["local demo"])

    @router.get("/paths")
    def demo_paths() -> dict[str, object]:
        return {
            "paths": [definition.as_public_dict() for definition in DEMO_DEFINITIONS],
            "disclaimer": (
                "Deterministic POC rule checks only—not clinical validation, operational "
                "guidance, or protocol authority."
            ),
        }

    @router.get("/reviews/{session_id}")
    def session_review(session_id: str) -> dict[str, object]:
        try:
            safe_session_id = ensure_safe_identifier(session_id, "session_id")
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        log_path = session_manager.logger.path_for(safe_session_id)
        if not log_path.is_file():
            raise HTTPException(status_code=404, detail="Session log was not found.")
        try:
            summary = generate_review_summary(log_path)
        except ValueError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        return {"review": summary, "log_name": log_path.name}

    return router
