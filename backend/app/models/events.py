"""Inbound trainee event models."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TraineeActionEvent(BaseModel):
    """One normalized, manually or programmatically stubbed trainee action."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "0.1.0"
    session_id: str = Field(min_length=1)
    scenario_id: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    timestamp: datetime
    actor_id: str = Field(min_length=1)
    action_type: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    sequence_number: int = Field(ge=1)
