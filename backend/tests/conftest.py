"""Shared test message helpers."""

from datetime import datetime, timezone

from backend.app.models.events import TraineeActionEvent
from backend.app.models.messages import TraineeActionMessage


def action_message(
    session_id: str,
    action_type: str,
    sequence_number: int,
    scenario_id: str = "smoke_inhalation_room_v0",
) -> TraineeActionMessage:
    event_id = f"{session_id}-event-{sequence_number}"
    timestamp = datetime(2026, 1, 1, 0, 0, sequence_number, tzinfo=timezone.utc)
    event = TraineeActionEvent(
        session_id=session_id,
        scenario_id=scenario_id,
        event_id=event_id,
        timestamp=timestamp,
        actor_id="test-trainee",
        action_type=action_type,
        payload={},
        sequence_number=sequence_number,
    )
    return TraineeActionMessage(
        message_type="trainee_action",
        session_id=session_id,
        scenario_id=scenario_id,
        message_id=f"{session_id}-message-{sequence_number}",
        timestamp=timestamp,
        sequence_number=sequence_number,
        correlation_event_id=event_id,
        trainee_action=event,
    )
