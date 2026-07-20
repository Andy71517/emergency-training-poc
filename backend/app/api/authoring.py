"""HTTP boundary for the mocked instructor scenario-authoring workflow."""

from fastapi import APIRouter, HTTPException

from backend.app.authoring.models import (
    GenerationJob,
    ScenarioDraft,
    ScenarioDraftApproval,
    ScenarioDraftRejection,
    ScenarioDraftUpdate,
    ScenarioGenerationRequest,
)
from backend.app.authoring.service import (
    DraftNotFoundError,
    DraftRevisionConflictError,
    ScenarioAuthoringService,
)


def create_authoring_router(service: ScenarioAuthoringService) -> APIRouter:
    router = APIRouter(prefix="/api/authoring", tags=["mock scenario authoring"])

    @router.post("/jobs", response_model=GenerationJob)
    def create_mock_generation_job(request: ScenarioGenerationRequest) -> GenerationJob:
        return service.create_mock_job(request)

    @router.get("/drafts/{draft_id}", response_model=ScenarioDraft)
    def get_draft(draft_id: str) -> ScenarioDraft:
        try:
            return service.get_draft(draft_id)
        except DraftNotFoundError as error:
            raise HTTPException(status_code=404, detail="Scenario draft was not found.") from error

    @router.put("/drafts/{draft_id}", response_model=ScenarioDraft)
    def update_draft(draft_id: str, update: ScenarioDraftUpdate) -> ScenarioDraft:
        try:
            return service.update_draft(draft_id, update)
        except DraftNotFoundError as error:
            raise HTTPException(status_code=404, detail="Scenario draft was not found.") from error
        except DraftRevisionConflictError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    @router.post("/drafts/{draft_id}/approve", response_model=ScenarioDraft)
    def approve_draft(draft_id: str, approval: ScenarioDraftApproval) -> ScenarioDraft:
        try:
            return service.approve_draft(draft_id, approval)
        except DraftNotFoundError as error:
            raise HTTPException(status_code=404, detail="Scenario draft was not found.") from error
        except DraftRevisionConflictError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    @router.post("/drafts/{draft_id}/reject", response_model=ScenarioDraft)
    def reject_draft(draft_id: str, rejection: ScenarioDraftRejection) -> ScenarioDraft:
        try:
            return service.reject_draft(draft_id, rejection)
        except DraftNotFoundError as error:
            raise HTTPException(status_code=404, detail="Scenario draft was not found.") from error
        except DraftRevisionConflictError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    return router
