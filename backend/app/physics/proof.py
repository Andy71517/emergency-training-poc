"""Backend authorization and deterministic evaluation for the physics proof."""

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from backend.app.logging.jsonl_logger import JsonlSessionLogger
from backend.app.physics.models import (
    AcceptanceThresholds,
    BoxCollider,
    PhysicalMaterial,
    PhysicsAcceptanceResult,
    PhysicsAuthorizationRequest,
    PhysicsInteractionCommand,
    PhysicsObservation,
    PhysicsProofConfiguration,
    PhysicsTransform,
    Quaternion,
    Vector3,
)

SCENARIO_ID = "blocked_exit_hallway_v0"


def _box(
    collider_id: str,
    center: tuple[float, float, float],
    half_extents: tuple[float, float, float],
    *,
    is_static: bool = False,
) -> BoxCollider:
    return BoxCollider(
        collider_id=collider_id,
        center_m=Vector3(x=center[0], y=center[1], z=center[2]),
        half_extents_m=Vector3(x=half_extents[0], y=half_extents[1], z=half_extents[2]),
        is_static=is_static,
    )


def build_configuration() -> PhysicsProofConfiguration:
    return PhysicsProofConfiguration(
        proof_id="chair_movement_contact_v0",
        scenario_id=SCENARIO_ID,
        object_id="leather_chair_candidate_v0",
        units="metres_kilograms_seconds",
        gravity_mps2=Vector3(x=0.0, y=-9.81, z=0.0),
        fixed_timestep_seconds=1.0 / 60.0,
        object_mass_kg=12.0,
        linear_damping=0.35,
        angular_damping=0.50,
        chair_material=PhysicalMaterial(friction=0.65, restitution=0.05),
        floor_material=PhysicalMaterial(friction=0.75, restitution=0.05),
        initial_transform=PhysicsTransform(
            position_m=Vector3(x=-0.75, y=0.0, z=0.0),
            rotation=Quaternion(),
        ),
        chair_colliders=[
            _box("seat", (0.0, 0.55, 0.0), (0.32, 0.07, 0.32)),
            _box("back", (0.0, 0.90, 0.28), (0.32, 0.30, 0.06)),
            _box("front_left_leg", (-0.24, 0.25, -0.24), (0.04, 0.25, 0.04)),
            _box("front_right_leg", (0.24, 0.25, -0.24), (0.04, 0.25, 0.04)),
            _box("back_left_leg", (-0.24, 0.25, 0.24), (0.04, 0.25, 0.04)),
            _box("back_right_leg", (0.24, 0.25, 0.24), (0.04, 0.25, 0.04)),
        ],
        static_colliders=[
            _box("floor", (0.0, -0.05, 0.0), (3.0, 0.05, 3.0), is_static=True),
            _box("contact_barrier", (1.1, 0.6, 0.0), (0.08, 0.6, 1.0), is_static=True),
        ],
        impulse_ns=Vector3(x=40.0, y=0.0, z=0.0),
        impulse_application_point_m=Vector3(x=0.0, y=0.70, z=0.0),
        acceptance=AcceptanceThresholds(
            minimum_horizontal_movement_m=0.35,
            maximum_observation_seconds=10.0,
            floor_penetration_tolerance_m=0.01,
            required_contact_object_id="contact_barrier",
            settle_linear_speed_mps=0.08,
            settle_angular_speed_radps=0.12,
            settle_duration_seconds=0.75,
        ),
    )


class PhysicsProofService:
    """Keeps commands local and lets the backend judge client observations."""

    def __init__(self, log_directory: Path | None = None) -> None:
        self.configuration = build_configuration()
        self._commands: dict[str, PhysicsInteractionCommand] = {}
        self._logger = JsonlSessionLogger(log_directory or Path("logs/physics"))

    def authorize(self, request: PhysicsAuthorizationRequest) -> PhysicsInteractionCommand:
        if request.scenario_id != self.configuration.scenario_id:
            raise ValueError("This physics proof is not configured for that scenario.")
        command = PhysicsInteractionCommand(
            command_id=f"physics-{uuid4().hex}",
            session_id=request.session_id,
            scenario_id=request.scenario_id,
            proof_id=self.configuration.proof_id,
            object_id=self.configuration.object_id,
            command_type="apply_impulse",
            impulse_ns=self.configuration.impulse_ns,
            application_point_m=self.configuration.impulse_application_point_m,
            authorized_at=datetime.now(UTC),
        )
        self._commands[command.command_id] = command
        return command

    def evaluate(self, observation: PhysicsObservation) -> PhysicsAcceptanceResult:
        command = self._commands.get(observation.command_id)
        if command is None:
            raise LookupError("The physics command is unknown or was not authorized.")
        expected = (
            command.session_id,
            command.scenario_id,
            command.proof_id,
            command.object_id,
        )
        observed = (
            observation.session_id,
            observation.scenario_id,
            observation.proof_id,
            observation.object_id,
        )
        if observed != expected:
            raise ValueError("The observation does not match its authorized physics command.")

        thresholds = self.configuration.acceptance
        movement = (
            observation.horizontal_displacement_m
            >= thresholds.minimum_horizontal_movement_m
        )
        contact = any(
            item.object_id == observation.object_id
            and item.contacted_object_id == thresholds.required_contact_object_id
            and item.first_contact_seconds <= thresholds.maximum_observation_seconds
            for item in observation.contacts
        )
        stayed_above_floor = (
            observation.minimum_floor_clearance_m
            >= -thresholds.floor_penetration_tolerance_m
        )
        within_time = observation.elapsed_seconds <= thresholds.maximum_observation_seconds
        accepted = movement and contact and stayed_above_floor and within_time

        checks = [
            f"Movement: {'pass' if movement else 'fail'}",
            f"Barrier contact: {'pass' if contact else 'fail'}",
            f"Floor collision: {'pass' if stayed_above_floor else 'fail'}",
            f"Time window: {'pass' if within_time else 'fail'}",
            f"Settled state reported: {'yes' if observation.settled else 'no'}",
        ]
        summary = (
            "Physics proof accepted: movement, contact, floor collision, and timing passed."
            if accepted
            else "Physics proof needs review: one or more required checks did not pass."
        )
        result = PhysicsAcceptanceResult(
            command_id=command.command_id,
            accepted=accepted,
            movement_detected=movement,
            required_contact_detected=contact,
            stayed_above_floor=stayed_above_floor,
            completed_within_time=within_time,
            settled=observation.settled,
            summary=summary,
            checks=checks,
        )
        self._logger.append(
            command.session_id,
            {
                "record_type": "physics_proof",
                "configuration": self.configuration.model_dump(mode="json"),
                "command": command.model_dump(mode="json"),
                "observation": observation.model_dump(mode="json"),
                "result": result.model_dump(mode="json"),
            },
        )
        return result
