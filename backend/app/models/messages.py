"""WebSocket message contracts for the POC client boundary."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.app.models.events import TraineeActionEvent
from backend.app.models.state import ScenarioState
from backend.app.validation.models import ValidationResult


class StartSessionMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message_type: Literal["start_session"]
    scenario_id: str = "smoke_inhalation_room_v0"


class TraineeActionMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "0.1.0"
    message_type: Literal["trainee_action"]
    session_id: str
    scenario_id: str
    message_id: str
    timestamp: datetime
    sequence_number: int = Field(ge=1)
    correlation_event_id: str | None = None
    trainee_action: TraineeActionEvent


class SessionStartedMessage(BaseModel):
    message_type: Literal["session_started"] = "session_started"
    session_id: str
    scenario_id: str
    scenario_version: str
    sequence_number: int = 0
    state: dict[str, object]


class ScenarioStateUpdateMessage(BaseModel):
    message_type: Literal["scenario_state_update"] = "scenario_state_update"
    session_id: str
    scenario_id: str
    sequence_number: int
    scenario_state: ScenarioState
    validation_result: ValidationResult


class ScenarioEndedMessage(BaseModel):
    message_type: Literal["scenario_ended"] = "scenario_ended"
    session_id: str
    scenario_id: str
    sequence_number: int
    outcome: str
    final_state: dict[str, object]


class ErrorMessage(BaseModel):
    message_type: Literal["error"] = "error"
    code: str
    message: str
