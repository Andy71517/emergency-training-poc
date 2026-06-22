"""Coordinate one deterministic event transaction per session."""

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.app.logging.jsonl_logger import JsonlSessionLogger
from backend.app.models.messages import (
    ScenarioEndedMessage,
    ScenarioStateUpdateMessage,
    SessionStartedMessage,
    TraineeActionMessage,
)
from backend.app.models.state import ScenarioState
from backend.app.scenario_engine.engine import ScenarioEngine
from backend.app.scenario_engine.loader import load_scenario
from backend.app.validation.rules import load_rules
from backend.app.validation.validator import ScenarioValidator

DEFAULT_LOG_DIRECTORY = Path(__file__).resolve().parents[3] / "logs" / "sessions"


class SessionInputError(ValueError):
    pass


@dataclass
class SessionContext:
    session_id: str
    scenario_id: str
    scenario_version: str
    engine: ScenarioEngine
    validator: ScenarioValidator
    state: dict[str, Any]
    sequence_number: int = 0
    event_ids: set[str] = field(default_factory=set)
    ended: bool = False


@dataclass(frozen=True)
class ProcessedAction:
    update: ScenarioStateUpdateMessage
    ended: ScenarioEndedMessage | None


class SessionManager:
    def __init__(self, log_directory: Path = DEFAULT_LOG_DIRECTORY) -> None:
        self.logger = JsonlSessionLogger(log_directory)
        self.sessions: dict[str, SessionContext] = {}

    def start_session(
        self,
        session_id: str,
        scenario_id: str = "smoke_inhalation_room_v0",
    ) -> SessionStartedMessage:
        if session_id in self.sessions:
            raise SessionInputError(f"Session '{session_id}' is already active")
        scenario = load_scenario(scenario_id)
        engine = ScenarioEngine(scenario)
        context = SessionContext(
            session_id=session_id,
            scenario_id=scenario_id,
            scenario_version=scenario.version,
            engine=engine,
            validator=ScenarioValidator(scenario, load_rules(scenario_id)),
            state=engine.initial_state(),
        )
        self.sessions[session_id] = context
        started = SessionStartedMessage(
            session_id=session_id,
            scenario_id=scenario_id,
            scenario_version=scenario.version,
            state=deepcopy(context.state),
        )
        self._log(
            context,
            event_type="session_started",
            sequence_number=0,
            state_snapshot=context.state,
        )
        return started

    def process_action(self, session_id: str, message: TraineeActionMessage) -> ProcessedAction:
        context = self._context(session_id)
        event = message.trainee_action
        self._check_message(context, message)

        candidate = context.engine.preview_action(context.state, event.action_type)
        evaluation = context.validator.evaluate(
            event,
            current_state=context.state,
            candidate_state=candidate.state,
            transition_note=candidate.note,
        )

        context.sequence_number = event.sequence_number
        context.event_ids.add(event.event_id)
        if not evaluation.blocks_transition:
            context.state = candidate.state

        terminal_label = context.engine.terminal_label(context.state)
        scenario_state = ScenarioState(
            session_id=context.session_id,
            scenario_id=context.scenario_id,
            event_id=event.event_id,
            timestamp=event.timestamp,
            sequence_number=context.sequence_number,
            state=deepcopy(context.state),
            is_terminal=terminal_label is not None,
            next_expected_actions=context.engine.next_expected_actions(context.state),
        )
        update = ScenarioStateUpdateMessage(
            session_id=context.session_id,
            scenario_id=context.scenario_id,
            sequence_number=context.sequence_number,
            scenario_state=scenario_state,
            validation_result=evaluation.result,
        )
        self._log(
            context,
            event_type="action_processed",
            sequence_number=context.sequence_number,
            inbound_message=message.model_dump(mode="json"),
            validation_result=evaluation.result.model_dump(mode="json"),
            state_snapshot=context.state,
        )

        ended_message: ScenarioEndedMessage | None = None
        if terminal_label is not None:
            context.ended = True
            ended_message = ScenarioEndedMessage(
                session_id=context.session_id,
                scenario_id=context.scenario_id,
                sequence_number=context.sequence_number,
                outcome=terminal_label,
                final_state=deepcopy(context.state),
            )
            self._log(
                context,
                event_type="scenario_ended",
                sequence_number=context.sequence_number,
                state_snapshot=context.state,
            )
        return ProcessedAction(update=update, ended=ended_message)

    def _check_message(self, context: SessionContext, message: TraineeActionMessage) -> None:
        event = message.trainee_action
        if context.ended:
            raise SessionInputError("Scenario has already ended")
        if message.session_id != context.session_id or event.session_id != context.session_id:
            raise SessionInputError("Message session_id does not match the WebSocket session")
        if message.scenario_id != context.scenario_id or event.scenario_id != context.scenario_id:
            raise SessionInputError("Message scenario_id does not match the active scenario")
        if message.sequence_number != event.sequence_number:
            raise SessionInputError("Envelope and event sequence numbers do not match")
        expected = context.sequence_number + 1
        if event.sequence_number != expected:
            raise SessionInputError(f"Expected sequence_number {expected}")
        if event.event_id in context.event_ids:
            raise SessionInputError("Duplicate event_id")
        if message.correlation_event_id not in {None, event.event_id}:
            raise SessionInputError("correlation_event_id does not match event_id")

    def _context(self, session_id: str) -> SessionContext:
        try:
            return self.sessions[session_id]
        except KeyError as error:
            raise SessionInputError(f"Unknown session '{session_id}'") from error

    def _log(
        self,
        context: SessionContext,
        *,
        event_type: str,
        sequence_number: int,
        inbound_message: dict[str, Any] | None = None,
        validation_result: dict[str, Any] | None = None,
        state_snapshot: dict[str, Any] | None = None,
    ) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": context.session_id,
            "scenario_id": context.scenario_id,
            "sequence_number": sequence_number,
            "event_type": event_type,
        }
        if inbound_message is not None:
            entry["inbound_message"] = inbound_message
        if validation_result is not None:
            entry["validation_result"] = validation_result
        if state_snapshot is not None:
            entry["state_snapshot"] = deepcopy(state_snapshot)
        self.logger.append(context.session_id, entry)
