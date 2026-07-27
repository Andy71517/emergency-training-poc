"""Tests for backend-owned visual physics authorization and evaluation."""

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.physics.models import (
    PhysicsContactObservation,
    PhysicsEngineIdentity,
    PhysicsAuthorizationRequest,
    PhysicsObservation,
    PhysicsTransform,
    Quaternion,
    Vector3,
)
from backend.app.physics.proof import PhysicsProofService


def make_observation(
    service: PhysicsProofService,
    *,
    displacement: float = 0.60,
    include_barrier_contact: bool = True,
    floor_clearance: float = 0.0,
    elapsed_seconds: float = 2.5,
) -> PhysicsObservation:
    command = service.authorize(
        PhysicsAuthorizationRequest(
            session_id="physics-test-session",
            scenario_id="blocked_exit_hallway_v0",
        )
    )
    started = datetime.now(UTC)
    contacts = (
        [
            PhysicsContactObservation(
                object_id=command.object_id,
                contacted_object_id="contact_barrier",
                first_contact_seconds=1.2,
            )
        ]
        if include_barrier_contact
        else []
    )
    return PhysicsObservation(
        command_id=command.command_id,
        session_id=command.session_id,
        scenario_id=command.scenario_id,
        proof_id=command.proof_id,
        object_id=command.object_id,
        engine=PhysicsEngineIdentity(
            client_name="pytest",
            engine_name="deterministic-fixture",
            engine_version="0.1",
        ),
        started_at=started,
        completed_at=started + timedelta(seconds=elapsed_seconds),
        elapsed_seconds=elapsed_seconds,
        initial_transform=service.configuration.initial_transform,
        final_transform=PhysicsTransform(
            position_m=Vector3(x=-0.75 + displacement, y=0.0, z=0.0),
            rotation=Quaternion(),
        ),
        horizontal_displacement_m=displacement,
        minimum_floor_clearance_m=floor_clearance,
        contacts=contacts,
        settled=True,
        evidence_notes=["Synthetic test observation."],
    )


def test_configuration_has_shared_constants_and_colliders() -> None:
    configuration = PhysicsProofService().configuration

    assert configuration.gravity_mps2.y == -9.81
    assert configuration.object_mass_kg == 12.0
    assert configuration.fixed_timestep_seconds == 1.0 / 60.0
    assert configuration.impulse_ns.x == 14.0
    assert {item.collider_id for item in configuration.static_colliders} == {
        "floor",
        "contact_barrier",
    }


def test_backend_accepts_movement_contact_and_floor_collision_evidence() -> None:
    service = PhysicsProofService()

    result = service.evaluate(make_observation(service))

    assert result.accepted is True
    assert result.movement_detected is True
    assert result.required_contact_detected is True
    assert result.stayed_above_floor is True


def test_backend_rejects_observation_without_required_contact() -> None:
    service = PhysicsProofService()

    result = service.evaluate(make_observation(service, include_barrier_contact=False))

    assert result.accepted is False
    assert result.required_contact_detected is False


def test_physics_api_authorizes_and_evaluates_a_known_command(tmp_path) -> None:
    app = create_app(tmp_path)
    client = TestClient(app)
    configuration = client.get("/api/physics/proof/configuration")
    authorization = client.post(
        "/api/physics/proof/authorize",
        json={
            "session_id": "browser-physics-test",
            "scenario_id": "blocked_exit_hallway_v0",
        },
    )

    assert configuration.status_code == 200
    assert configuration.json()["object_mass_kg"] == 12.0
    assert authorization.status_code == 200

    service = app.state.physics_service
    observation = make_observation(service)
    response = client.post(
        "/api/physics/proof/observations",
        json=observation.model_dump(mode="json"),
    )

    assert response.status_code == 200
    assert response.json()["accepted"] is True


def test_physics_api_rejects_unknown_command(tmp_path) -> None:
    app = create_app(tmp_path)
    client = TestClient(app)
    service = app.state.physics_service
    observation = make_observation(service)
    observation.command_id = "physics-unknown"

    response = client.post(
        "/api/physics/proof/observations",
        json=observation.model_dump(mode="json"),
    )

    assert response.status_code == 404
