from pathlib import Path

from backend.app.orchestrator.session_manager import SessionManager
from backend.app.scenario_engine.engine import ScenarioEngine
from backend.app.scenario_engine.loader import load_scenario
from backend.tests.conftest import action_message


def test_scenario_yaml_loads_and_initial_state_is_correct() -> None:
    scenario = load_scenario()

    assert scenario.scenario_id == "smoke_inhalation_room_v0"
    assert scenario.initial_state["phase"] == "awaiting_assessment"
    assert scenario.initial_state["scenario_outcome"] == "in_progress"
    assert scenario.initial_state["scene_assessed"] is False


def test_happy_path_reaches_expected_final_state(tmp_path: Path) -> None:
    manager = SessionManager(tmp_path)
    session_id = "happy-test"
    manager.start_session(session_id)
    actions = ["assess_scene", "confirm_ppe", "request_backup", "enter_room", "remove_occupant"]

    result = None
    for sequence_number, action in enumerate(actions, start=1):
        result = manager.process_action(session_id, action_message(session_id, action, sequence_number))

    assert result is not None
    assert result.update.validation_result.status == "ok"
    assert result.update.scenario_state.state["scenario_outcome"] == "completed"
    assert result.update.scenario_state.state["occupant_removed"] is True
    assert result.ended is not None
    assert result.ended.outcome == "completed"


def test_wrong_sequence_produces_warning_or_error_without_transition(tmp_path: Path) -> None:
    manager = SessionManager(tmp_path)
    session_id = "wrong-sequence-test"
    manager.start_session(session_id)

    warning = manager.process_action(session_id, action_message(session_id, "confirm_ppe", 1))
    error = manager.process_action(session_id, action_message(session_id, "enter_room", 2))

    assert warning.update.validation_result.status == "warning"
    assert warning.update.scenario_state.state["ppe_confirmed"] is False
    assert error.update.validation_result.status == "error"
    assert error.update.scenario_state.state["phase"] == "awaiting_assessment"


def test_disallowed_action_produces_error(tmp_path: Path) -> None:
    manager = SessionManager(tmp_path)
    session_id = "unknown-action-test"
    manager.start_session(session_id)

    result = manager.process_action(session_id, action_message(session_id, "teleport", 1))

    assert result.update.validation_result.status == "error"
    assert result.update.validation_result.errors[0].code == "unknown_action"
    assert result.update.scenario_state.state["phase"] == "awaiting_assessment"


def test_engine_is_deterministic_for_ordered_actions() -> None:
    scenario = load_scenario()
    actions = ["assess_scene", "confirm_ppe", "request_backup", "enter_room", "remove_occupant"]

    def run() -> dict[str, object]:
        engine = ScenarioEngine(scenario)
        state = engine.initial_state()
        for action in actions:
            state = engine.preview_action(state, action).state
        return state

    assert run() == run()
