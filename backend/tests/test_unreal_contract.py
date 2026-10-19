import json
from pathlib import Path

from backend.app.models.messages import (
    ScenarioEndedMessage,
    ScenarioStateUpdateMessage,
    StartSessionMessage,
)
from scripts.run_unreal_contract_harness import ClientPhase, UnrealClientStateMachine

CONTRACT_EXAMPLES = Path("unreal/contract/examples")


def load_example(name: str) -> dict[str, object]:
    return json.loads((CONTRACT_EXAMPLES / name).read_text(encoding="utf-8"))


def test_unreal_contract_examples_match_backend_models() -> None:
    StartSessionMessage.model_validate(load_example("start_session.message.json"))
    ScenarioStateUpdateMessage.model_validate(load_example("scenario_state_update.message.json"))
    ScenarioStateUpdateMessage.model_validate(load_example("validation_error_state_update.message.json"))
    ScenarioEndedMessage.model_validate(load_example("scenario_ended.message.json"))


def test_unreal_client_state_machine_accepts_expected_lifecycle() -> None:
    state_machine = UnrealClientStateMachine()

    state_machine.begin_connect()
    state_machine.socket_opened()
    state_machine.handle_server_message({"message_type": "session_started"})

    assert state_machine.phase == ClientPhase.READY_FOR_ACTION

    state_machine.action_sent()
    state_machine.handle_server_message({"message_type": "scenario_state_update", "scenario_state": {"is_terminal": False}})

    assert state_machine.phase == ClientPhase.READY_FOR_ACTION

    state_machine.action_sent()
    state_machine.handle_server_message({"message_type": "scenario_state_update", "scenario_state": {"is_terminal": True}})

    assert state_machine.phase == ClientPhase.WAITING_FOR_SCENARIO_END

    state_machine.handle_server_message({"message_type": "scenario_ended"})

    assert state_machine.phase == ClientPhase.ENDED


def test_unreal_client_state_machine_stops_on_backend_error() -> None:
    state_machine = UnrealClientStateMachine()
    state_machine.begin_connect()
    state_machine.socket_opened()

    state_machine.handle_server_message({"message_type": "error", "code": "invalid_message"})

    assert state_machine.phase == ClientPhase.ERROR
