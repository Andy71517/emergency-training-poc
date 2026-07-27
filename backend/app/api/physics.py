"""Local HTTP boundary for the browser physics proof."""

from fastapi import APIRouter, HTTPException

from backend.app.physics.models import (
    PhysicsAcceptanceResult,
    PhysicsAuthorizationRequest,
    PhysicsInteractionCommand,
    PhysicsObservation,
    PhysicsProofConfiguration,
)
from backend.app.physics.proof import PhysicsProofService


def create_physics_router(service: PhysicsProofService) -> APIRouter:
    router = APIRouter(prefix="/api/physics/proof", tags=["visual physics proof"])

    @router.get("/configuration", response_model=PhysicsProofConfiguration)
    def get_configuration() -> PhysicsProofConfiguration:
        return service.configuration

    @router.post("/authorize", response_model=PhysicsInteractionCommand)
    def authorize(request: PhysicsAuthorizationRequest) -> PhysicsInteractionCommand:
        try:
            return service.authorize(request)
        except ValueError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    @router.post("/observations", response_model=PhysicsAcceptanceResult)
    def submit_observation(observation: PhysicsObservation) -> PhysicsAcceptanceResult:
        try:
            return service.evaluate(observation)
        except LookupError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except ValueError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    return router
