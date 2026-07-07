from pathlib import Path
import json

from backend.app.orchestrator.session_manager import SessionManager
from backend.app.scenario_engine.engine import ScenarioEngine
from backend.app.scenario_engine.loader import load_scenario
from backend.tests.conftest import action_message
from jsonschema import Draft202012Validator


def test_scenario_yaml_loads_and_initial_state_is_correct() -> None:
    scenario = load_scenario()

    assert scenario.scenario_id == "smoke_inhalation_room_v0"
    assert scenario.initial_state["phase"] == "awaiting_assessment"
    assert scenario.initial_state["scenario_outcome"] == "in_progress"
    assert scenario.initial_state["scene_assessed"] is False
    assert scenario.initial_state["room_scanned"] is False
    assert scenario.initial_state["path_blocked"] is True
    assert scenario.initial_state["door_open"] is False
    assert scenario.initial_state["exit_path_clear"] is False
    assert scenario.initial_state["visibility_checked"] is False
    assert scenario.initial_state["status_communicated"] is False
    assert scenario.initial_state["environment_monitored"] is False
    assert scenario.initial_state["occupant_visible"] is False
    assert scenario.initial_state["occupant_located"] is False
    assert scenario.initial_state["environment"]["smoke_density"] == "moderate_preview"
    assert scenario.initial_state["environment"]["visibility_level"] == "poor_preview"
    assert scenario.initial_state["environment"]["objects"]["wooden_chair_poc"]["blocks_path"] is True
    assert scenario.initial_state["environment"]["objects"]["entry_door_poc"]["open_state"] == "closed"
    assert scenario.initial_state["environment"]["objects"]["entry_door_poc"]["locked"] is False
    visibility = scenario.initial_state["environment"]["objects"]["smoke_visibility_cue_poc"]
    assert visibility["observed"] is False
    assert visibility["visibility_level"] == "low"


def test_environment_objects_follow_shared_contract() -> None:
    scenario = load_scenario()
    schema = json.loads(Path("schemas/events/environment_object.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)

    for object_id, object_state in scenario.initial_state["environment"]["objects"].items():
        validator.validate(object_state)
        assert object_id.endswith("_poc")
        assert object_state["label"]
        assert object_state["location"]
        assert object_state["physics_enabled"] is False
        assert "real" in object_state["physics_note"].lower()


def test_happy_path_reaches_expected_final_state(tmp_path: Path) -> None:
    manager = SessionManager(tmp_path)
    session_id = "happy-test"
    manager.start_session(session_id)
    actions = [
        "assess_scene",
        "scan_room",
        "check_door",
        "confirm_ppe",
        "request_backup",
        "communicate_status",
        "move_obstacle",
        "open_door",
        "check_visibility",
        "monitor_environment",
        "enter_room",
        "locate_occupant",
        "remove_occupant",
    ]

    result = None
    for sequence_number, action in enumerate(actions, start=1):
        result = manager.process_action(session_id, action_message(session_id, action, sequence_number))

    assert result is not None
    assert result.update.validation_result.status == "ok"
    assert result.update.scenario_state.state["scenario_outcome"] == "completed"
    assert result.update.scenario_state.state["occupant_removed"] is True
    assert result.update.scenario_state.state["occupant_visible"] is True
    assert result.update.scenario_state.state["occupant_located"] is True
    assert result.update.scenario_state.state["exit_path_clear"] is True
    chair = result.update.scenario_state.state["environment"]["objects"]["wooden_chair_poc"]
    door = result.update.scenario_state.state["environment"]["objects"]["entry_door_poc"]
    visibility = result.update.scenario_state.state["environment"]["objects"]["smoke_visibility_cue_poc"]
    assert chair["blocks_path"] is False
    assert chair["moved"] is True
    assert door["open_state"] == "open"
    assert door["locked"] is False
    assert visibility["observed"] is True
    assert visibility["visibility_level"] == "checked_low_visibility"
    assert result.update.scenario_state.state["environment"]["cues"]["occupant_search"]["observed"] is True
    assert result.ended is not None
    assert result.ended.outcome == "completed"


def test_move_obstacle_clears_wooden_chair_path_block(tmp_path: Path) -> None:
    manager = SessionManager(tmp_path)
    session_id = "chair-move-test"
    manager.start_session(session_id)
    manager.process_action(session_id, action_message(session_id, "assess_scene", 1))
    manager.process_action(session_id, action_message(session_id, "scan_room", 2))

    result = manager.process_action(session_id, action_message(session_id, "move_obstacle", 3))
    state = result.update.scenario_state.state
    chair = state["environment"]["objects"]["wooden_chair_poc"]

    assert result.update.validation_result.status == "ok"
    assert state["path_blocked"] is False
    assert state["exit_path_clear"] is False
    assert chair["blocks_path"] is False
    assert chair["moved"] is True
    assert chair["location"] == "clear_of_entry_path"


def test_open_door_updates_door_state_without_using_lock_metadata(tmp_path: Path) -> None:
    manager = SessionManager(tmp_path)
    session_id = "door-open-test"
    manager.start_session(session_id)
    manager.process_action(session_id, action_message(session_id, "assess_scene", 1))
    manager.process_action(session_id, action_message(session_id, "scan_room", 2))
    manager.process_action(session_id, action_message(session_id, "check_door", 3))

    result = manager.process_action(session_id, action_message(session_id, "open_door", 4))
    state = result.update.scenario_state.state
    door = state["environment"]["objects"]["entry_door_poc"]

    assert result.update.validation_result.status == "ok"
    assert state["door_open"] is True
    assert door["open_state"] == "open"
    assert door["blocks_path"] is False
    assert door["locked"] is False
    assert door["door_type"] == "hinged_wooden_door_preview"


def test_check_visibility_marks_smoke_visibility_cue_observed(tmp_path: Path) -> None:
    manager = SessionManager(tmp_path)
    session_id = "visibility-check-test"
    manager.start_session(session_id)
    manager.process_action(session_id, action_message(session_id, "assess_scene", 1))
    manager.process_action(session_id, action_message(session_id, "scan_room", 2))

    result = manager.process_action(session_id, action_message(session_id, "check_visibility", 3))
    state = result.update.scenario_state.state
    visibility = state["environment"]["objects"]["smoke_visibility_cue_poc"]

    assert result.update.validation_result.status == "ok"
    assert state["visibility_checked"] is True
    assert visibility["observed"] is True
    assert visibility["visibility_level"] == "checked_low_visibility"
    assert state["environment"]["visibility_level"] == "checked_low_visibility"


def test_room_scan_is_required_before_environment_object_work(tmp_path: Path) -> None:
    manager = SessionManager(tmp_path)
    session_id = "room-scan-warning-test"
    manager.start_session(session_id)
    manager.process_action(session_id, action_message(session_id, "assess_scene", 1))

    result = manager.process_action(session_id, action_message(session_id, "move_obstacle", 2))

    assert result.update.validation_result.status == "warning"
    assert result.update.validation_result.warnings[0].code == "room_scan_not_recorded"
    assert result.update.validation_result.warnings[0].instructor_note
    assert result.update.scenario_state.state["path_blocked"] is True


def test_door_check_warning_does_not_block_open_door_transition(tmp_path: Path) -> None:
    manager = SessionManager(tmp_path)
    session_id = "door-check-warning-test"
    manager.start_session(session_id)
    manager.process_action(session_id, action_message(session_id, "assess_scene", 1))
    manager.process_action(session_id, action_message(session_id, "scan_room", 2))

    result = manager.process_action(session_id, action_message(session_id, "open_door", 3))

    assert result.update.validation_result.status == "warning"
    assert result.update.validation_result.warnings[0].code == "door_check_not_recorded"
    assert result.update.scenario_state.state["door_open"] is True


def test_entering_before_moving_chair_produces_warning_without_transition(tmp_path: Path) -> None:
    manager = SessionManager(tmp_path)
    session_id = "chair-warning-test"
    manager.start_session(session_id)
    actions = ["assess_scene", "scan_room", "confirm_ppe", "request_backup", "communicate_status", "enter_room"]

    result = None
    for sequence_number, action in enumerate(actions, start=1):
        result = manager.process_action(session_id, action_message(session_id, action, sequence_number))

    assert result is not None
    assert result.update.validation_result.status == "warning"
    assert result.update.validation_result.warnings[0].code == "environmental_cue_not_cleared"
    assert result.update.scenario_state.state["phase"] == "scene_assessed"
    assert result.update.scenario_state.state["path_blocked"] is True


def test_entering_before_opening_door_produces_warning_without_transition(tmp_path: Path) -> None:
    manager = SessionManager(tmp_path)
    session_id = "door-warning-test"
    manager.start_session(session_id)
    actions = [
        "assess_scene",
        "scan_room",
        "confirm_ppe",
        "request_backup",
        "communicate_status",
        "move_obstacle",
        "enter_room",
    ]

    result = None
    for sequence_number, action in enumerate(actions, start=1):
        result = manager.process_action(session_id, action_message(session_id, action, sequence_number))

    assert result is not None
    assert result.update.validation_result.status == "warning"
    assert result.update.validation_result.warnings[0].code == "entry_door_still_closed"
    assert result.update.scenario_state.state["phase"] == "scene_assessed"
    assert result.update.scenario_state.state["door_open"] is False


def test_entering_before_checking_visibility_produces_warning_without_transition(
    tmp_path: Path,
) -> None:
    manager = SessionManager(tmp_path)
    session_id = "visibility-warning-test"
    manager.start_session(session_id)
    actions = [
        "assess_scene",
        "scan_room",
        "confirm_ppe",
        "request_backup",
        "communicate_status",
        "move_obstacle",
        "open_door",
        "enter_room",
    ]

    result = None
    for sequence_number, action in enumerate(actions, start=1):
        result = manager.process_action(session_id, action_message(session_id, action, sequence_number))

    assert result is not None
    assert result.update.validation_result.status == "warning"
    assert result.update.validation_result.warnings[0].code == "visibility_cue_not_checked"
    assert result.update.scenario_state.state["phase"] == "scene_assessed"
    assert result.update.scenario_state.state["visibility_checked"] is False


def test_entering_before_communicating_status_produces_warning_without_transition(
    tmp_path: Path,
) -> None:
    manager = SessionManager(tmp_path)
    session_id = "communication-warning-test"
    manager.start_session(session_id)
    actions = [
        "assess_scene",
        "scan_room",
        "confirm_ppe",
        "request_backup",
        "move_obstacle",
        "open_door",
        "check_visibility",
        "monitor_environment",
        "enter_room",
    ]

    result = None
    for sequence_number, action in enumerate(actions, start=1):
        result = manager.process_action(session_id, action_message(session_id, action, sequence_number))

    assert result is not None
    assert result.update.validation_result.status == "warning"
    assert result.update.validation_result.warnings[0].code == "status_not_communicated"
    assert result.update.scenario_state.state["phase"] == "scene_assessed"


def test_entering_before_monitoring_environment_produces_warning_without_transition(
    tmp_path: Path,
) -> None:
    manager = SessionManager(tmp_path)
    session_id = "environment-monitor-warning-test"
    manager.start_session(session_id)
    actions = [
        "assess_scene",
        "scan_room",
        "confirm_ppe",
        "request_backup",
        "communicate_status",
        "move_obstacle",
        "open_door",
        "check_visibility",
        "enter_room",
    ]

    result = None
    for sequence_number, action in enumerate(actions, start=1):
        result = manager.process_action(session_id, action_message(session_id, action, sequence_number))

    assert result is not None
    assert result.update.validation_result.status == "warning"
    assert result.update.validation_result.warnings[0].code == "environment_not_monitored"
    assert result.update.scenario_state.state["phase"] == "scene_assessed"


def test_removing_occupant_before_locating_them_produces_error_without_transition(
    tmp_path: Path,
) -> None:
    manager = SessionManager(tmp_path)
    session_id = "occupant-location-error-test"
    manager.start_session(session_id)
    actions = [
        "assess_scene",
        "scan_room",
        "confirm_ppe",
        "request_backup",
        "communicate_status",
        "move_obstacle",
        "open_door",
        "check_visibility",
        "monitor_environment",
        "enter_room",
        "remove_occupant",
    ]

    result = None
    for sequence_number, action in enumerate(actions, start=1):
        result = manager.process_action(session_id, action_message(session_id, action, sequence_number))

    assert result is not None
    assert result.update.validation_result.status == "error"
    assert result.update.validation_result.errors[0].code == "occupant_not_located"
    assert result.update.scenario_state.state["phase"] == "room_entered"


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
        "scan_room",
        "check_door",
        "confirm_ppe",
        "request_backup",
        "communicate_status",
        "move_obstacle",
        "open_door",
        "check_visibility",
        "monitor_environment",
        "enter_room",
        "locate_occupant",
        "remove_occupant",
    ]

    def run() -> dict[str, object]:
        engine = ScenarioEngine(scenario)
        state = engine.initial_state()
        for action in actions:
            state = engine.preview_action(state, action).state
        return state

    assert run() == run()
