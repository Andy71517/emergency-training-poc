"""Inbound trainee event models."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.security import (
    SCHEMA_VERSION,
    ensure_safe_action_type,
    ensure_safe_identifier,
    ensure_safe_payload,
    ensure_safe_scenario_id,
)


class TraineeActionEvent(BaseModel):
    """One normalized, manually or programmatically stubbed trainee action."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["0.1.0"] = SCHEMA_VERSION
    session_id: str = Field(min_length=1)
    scenario_id: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    timestamp: datetime
    actor_id: str = Field(min_length=1)
    action_type: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    sequence_number: int = Field(ge=1)

    @field_validator("session_id", "event_id", "actor_id")
    @classmethod
    def _safe_identifier(cls, value: str, info: Any) -> str:
        return ensure_safe_identifier(value, info.field_name)

    @field_validator("scenario_id")
    @classmethod
    def _safe_scenario_id(cls, value: str) -> str:
        return ensure_safe_scenario_id(value)

    @field_validator("action_type")
    @classmethod
    def _safe_action_type(cls, value: str) -> str:
        return ensure_safe_action_type(value)

    @field_validator("payload")
    @classmethod
    def _safe_payload(cls, value: dict[str, Any]) -> dict[str, Any]:
        return ensure_safe_payload(value)
