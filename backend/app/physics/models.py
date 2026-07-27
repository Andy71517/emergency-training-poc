"""Strict request and response models for the visual physics proof."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from backend.app.security import ensure_safe_identifier, ensure_safe_scenario_id

PHYSICS_CONTRACT_VERSION = "0.1.0"


class StrictPhysicsModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Vector3(StrictPhysicsModel):
    x: float
    y: float
    z: float


class Quaternion(StrictPhysicsModel):
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    w: float = 1.0


class PhysicsTransform(StrictPhysicsModel):
    position_m: Vector3
    rotation: Quaternion = Field(default_factory=Quaternion)


class BoxCollider(StrictPhysicsModel):
    collider_id: str
    center_m: Vector3
    half_extents_m: Vector3
    is_static: bool = False


class PhysicalMaterial(StrictPhysicsModel):
    friction: float = Field(ge=0.0)
    restitution: float = Field(ge=0.0, le=1.0)


class AcceptanceThresholds(StrictPhysicsModel):
    minimum_horizontal_movement_m: float = Field(gt=0.0)
    maximum_observation_seconds: float = Field(gt=0.0)
    floor_penetration_tolerance_m: float = Field(ge=0.0)
    required_contact_object_id: str
    settle_linear_speed_mps: float = Field(gt=0.0)
    settle_angular_speed_radps: float = Field(gt=0.0)
    settle_duration_seconds: float = Field(gt=0.0)


class PhysicsProofConfiguration(StrictPhysicsModel):
    contract_version: Literal["0.1.0"] = PHYSICS_CONTRACT_VERSION
    proof_id: Literal["chair_movement_contact_v0"]
    scenario_id: str
    object_id: Literal["leather_chair_candidate_v0"]
    units: Literal["metres_kilograms_seconds"]
    gravity_mps2: Vector3
    fixed_timestep_seconds: float = Field(gt=0.0)
    object_mass_kg: float = Field(gt=0.0)
    linear_damping: float = Field(ge=0.0)
    angular_damping: float = Field(ge=0.0)
    chair_material: PhysicalMaterial
    floor_material: PhysicalMaterial
    initial_transform: PhysicsTransform
    chair_colliders: list[BoxCollider] = Field(min_length=1)
    static_colliders: list[BoxCollider] = Field(min_length=2)
    impulse_ns: Vector3
    impulse_application_point_m: Vector3
    acceptance: AcceptanceThresholds

    @field_validator("scenario_id")
    @classmethod
    def safe_scenario_id(cls, value: str) -> str:
        return ensure_safe_scenario_id(value)


class PhysicsAuthorizationRequest(StrictPhysicsModel):
    session_id: str
    scenario_id: str

    @field_validator("session_id")
    @classmethod
    def safe_session_id(cls, value: str) -> str:
        return ensure_safe_identifier(value, "session_id")

    @field_validator("scenario_id")
    @classmethod
    def safe_scenario_id(cls, value: str) -> str:
        return ensure_safe_scenario_id(value)


class PhysicsInteractionCommand(StrictPhysicsModel):
    contract_version: Literal["0.1.0"] = PHYSICS_CONTRACT_VERSION
    command_id: str
    session_id: str
    scenario_id: str
    proof_id: Literal["chair_movement_contact_v0"]
    object_id: Literal["leather_chair_candidate_v0"]
    command_type: Literal["apply_impulse"]
    impulse_ns: Vector3
    application_point_m: Vector3
    authorized_at: datetime

    @field_validator("command_id", "session_id")
    @classmethod
    def safe_identifiers(cls, value: str, info: Any) -> str:
        return ensure_safe_identifier(value, info.field_name)

    @field_validator("scenario_id")
    @classmethod
    def safe_scenario_id(cls, value: str) -> str:
        return ensure_safe_scenario_id(value)


class PhysicsEngineIdentity(StrictPhysicsModel):
    client_name: str = Field(min_length=1, max_length=80)
    engine_name: str = Field(min_length=1, max_length=80)
    engine_version: str = Field(min_length=1, max_length=40)


class PhysicsContactObservation(StrictPhysicsModel):
    object_id: str
    contacted_object_id: str
    first_contact_seconds: float = Field(ge=0.0)


class PhysicsObservation(StrictPhysicsModel):
    contract_version: Literal["0.1.0"] = PHYSICS_CONTRACT_VERSION
    command_id: str
    session_id: str
    scenario_id: str
    proof_id: Literal["chair_movement_contact_v0"]
    object_id: Literal["leather_chair_candidate_v0"]
    engine: PhysicsEngineIdentity
    started_at: datetime
    completed_at: datetime
    elapsed_seconds: float = Field(ge=0.0)
    initial_transform: PhysicsTransform
    final_transform: PhysicsTransform
    horizontal_displacement_m: float = Field(ge=0.0)
    minimum_floor_clearance_m: float
    contacts: list[PhysicsContactObservation] = Field(default_factory=list)
    settled: bool
    evidence_notes: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("command_id", "session_id")
    @classmethod
    def safe_identifiers(cls, value: str, info: Any) -> str:
        return ensure_safe_identifier(value, info.field_name)

    @field_validator("scenario_id")
    @classmethod
    def safe_scenario_id(cls, value: str) -> str:
        return ensure_safe_scenario_id(value)

    @model_validator(mode="after")
    def completed_after_start(self) -> "PhysicsObservation":
        if self.completed_at < self.started_at:
            raise ValueError("completed_at must not be earlier than started_at")
        return self


class PhysicsAcceptanceResult(StrictPhysicsModel):
    contract_version: Literal["0.1.0"] = PHYSICS_CONTRACT_VERSION
    command_id: str
    accepted: bool
    movement_detected: bool
    required_contact_detected: bool
    stayed_above_floor: bool
    completed_within_time: bool
    settled: bool
    summary: str
    checks: list[str]
