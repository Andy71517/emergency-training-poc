"""Client-neutral scenario state models."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ScenarioState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "0.1.0"
    session_id: str
    scenario_id: str
    event_id: str
    timestamp: datetime
    sequence_number: int = Field(ge=0)
    state: dict[str, Any]
    is_terminal: bool
    next_expected_actions: list[str]
