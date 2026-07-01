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
    assert scenario.initial_state["path_blocked"] is True
    assert scenario.initial_state["environment"]["objects"]["wooden_chair_poc"]["blocks_path"] is True


def test_happy_path_reaches_expected_final_state(tmp_path: Path) -> None:
    manager = SessionManager(tmp_path)
    session_id = "happy-test"
    manager.start_session(session_id)
    actions = [
        "assess_scene",
        "confirm_ppe",
        "request_backup",
        "move_obstacle",
        "enter_room",
        "remove_occupant",
    ]

    result = None
    for sequence_number, action in enumerate(actions, start=1):
        result = manager.process_action(session_id, action_message(session_id, action, sequence_number))

    assert result is not None
    assert result.update.validation_result.status == "ok"
    assert result.update.scenario_state.state["scenario_outcome"] == "completed"
    assert result.update.scenario_state.state["occupant_removed"] is True
    chair = result.update.scenario_state.state["environment"]["objects"]["wooden_chair_poc"]
    assert chair["blocks_path"] is False
    assert chair["moved"] is True
    assert result.ended is not None
    assert result.ended.outcome == "completed"


def test_move_obstacle_clears_wooden_chair_path_block(tmp_path: Path) -> None:
    manager = SessionManager(tmp_path)
    session_id = "chair-move-test"
    manager.start_session(session_id)
    manager.process_action(session_id, action_message(session_id, "assess_scene", 1))

    result = manager.process_action(session_id, action_message(session_id, "move_obstacle", 2))
    state = result.update.scenario_state.state
    chair = state["environment"]["objects"]["wooden_chair_poc"]

    assert result.update.validation_result.status == "ok"
    assert state["path_blocked"] is False
    assert chair["blocks_path"] is False
    assert chair["moved"] is True
    assert chair["location"] == "clear_of_entry_path"


def test_entering_before_moving_chair_produces_warning_without_transition(tmp_path: Path) -> None:
    manager = SessionManager(tmp_path)
    session_id = "chair-warning-test"
    manager.start_session(session_id)
    actions = ["assess_scene", "confirm_ppe", "request_backup", "enter_room"]

    result = None
    for sequence_number, action in enumerate(actions, start=1):
        result = manager.process_action(session_id, action_message(session_id, action, sequence_number))

    assert result is not None
    assert result.update.validation_result.status == "warning"
    assert result.update.validation_result.warnings[0].code == "environmental_cue_not_cleared"
    assert result.update.scenario_state.state["phase"] == "scene_assessed"
    assert result.update.scenario_state.state["path_blocked"] is True


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
    actions = [
        "assess_scene",
        "confirm_ppe",
        "request_backup",
        "move_obstacle",
        "enter_room",
        "remove_occupant",
    ]

    def run() -> dict[str, object]:
        engine = ScenarioEngine(scenario)
        state = engine.initial_state()
        for action in actions:
            state = engine.preview_action(state, action).state
        return state

    assert run() == run()
