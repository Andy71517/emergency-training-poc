"""Build contract-shaped messages for manual or scripted POC input."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from backend.app.models.events import TraineeActionEvent
from backend.app.models.messages import TraineeActionMessage


def build_action_message(
    *,
    session_id: str,
    action_type: str,
    sequence_number: int,
    scenario_id: str = "smoke_inhalation_room_v0",
    actor_id: str = "stub-trainee",
    payload: dict[str, Any] | None = None,
) -> TraineeActionMessage:
    now = datetime.now(timezone.utc)
    event_id = f"event-{uuid4()}"
    event = TraineeActionEvent(
        session_id=session_id,
        scenario_id=scenario_id,
        event_id=event_id,
        timestamp=now,
        actor_id=actor_id,
        action_type=action_type,
        payload=payload or {},
        sequence_number=sequence_number,
    )
    return TraineeActionMessage(
        message_type="trainee_action",
        session_id=session_id,
        scenario_id=scenario_id,
        message_id=f"message-{uuid4()}",
        timestamp=now,
        sequence_number=sequence_number,
        correlation_event_id=event_id,
        trainee_action=event,
    )
