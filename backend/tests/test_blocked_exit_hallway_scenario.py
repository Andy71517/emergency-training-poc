from pathlib import Path

from backend.app.logging.review_summary import format_review_summary, generate_review_summary
from backend.app.orchestrator.session_manager import SessionManager
from backend.app.scenario_engine.engine import ScenarioEngine
from backend.app.scenario_engine.loader import load_scenario
from backend.tests.conftest import action_message

SCENARIO_ID = "blocked_exit_hallway_v0"
HAPPY_PATH = [
    "assess_scene",
    "scan_hallway",
    "confirm_ppe",
    "request_backup",
    "communicate_status",
    "check_visibility",
    "identify_secondary_exit",
    "move_obstacle",
    "check_exit_door",
    "open_exit_door",
    "monitor_environment",
    "guide_occupant_to_exit",
]


def hallway_action(session_id: str, action_type: str, sequence_number: int):
    return action_message(session_id, action_type, sequence_number, scenario_id=SCENARIO_ID)


def test_blocked_exit_hallway_scenario_loads() -> None:
    scenario = load_scenario(SCENARIO_ID)

    assert scenario.scenario_id == SCENARIO_ID
    assert scenario.initial_state["phase"] == "awaiting_assessment"
    assert scenario.initial_state["primary_exit_blocked"] is True
    assert scenario.initial_state["exit_door_open"] is False
    assert scenario.initial_state["environment"]["objects"]["collapsed_bookshelf_poc"]["blocks_path"] is True
    assert scenario.initial_state["environment"]["objects"]["hallway_exit_door_poc"]["open_state"] == "closed"
    assert "guide_occupant_to_exit" in scenario.allowed_actions


def test_blocked_exit_hallway_happy_path_reaches_completed(tmp_path: Path) -> None:
    manager = SessionManager(tmp_path)
    session_id = "blocked-exit-happy"
    manager.start_session(session_id, SCENARIO_ID)

    result = None
    for sequence_number, action in enumerate(HAPPY_PATH, start=1):
        result = manager.process_action(session_id, hallway_action(session_id, action, sequence_number))

    assert result is not None
    state = result.update.scenario_state.state
    assert result.update.validation_result.status == "ok"
    assert state["scenario_outcome"] == "completed"
    assert state["phase"] == "occupant_exited"
    assert state["occupant_guided"] is True
    assert state["primary_exit_blocked"] is False
    assert state["exit_door_open"] is True
    assert state["environment"]["exit_path_clear"] is True
    assert state["environment"]["objects"]["collapsed_bookshelf_poc"]["moved"] is True
    assert state["environment"]["objects"]["hallway_exit_door_poc"]["open_state"] == "open"
    assert result.ended is not None
    assert result.ended.outcome == "completed"


def test_hallway_scan_required_before_exit_path_work(tmp_path: Path) -> None:
    manager = SessionManager(tmp_path)
    session_id = "hallway-scan-warning"
    manager.start_session(session_id, SCENARIO_ID)
    manager.process_action(session_id, hallway_action(session_id, "assess_scene", 1))

    result = manager.process_action(session_id, hallway_action(session_id, "move_obstacle", 2))

    assert result.update.validation_result.status == "warning"
    assert result.update.validation_result.warnings[0].code == "hallway_scan_not_recorded"
    assert result.update.validation_result.warnings[0].instructor_note
    assert result.update.scenario_state.state["primary_exit_blocked"] is True


def test_exit_door_check_required_before_opening(tmp_path: Path) -> None:
    manager = SessionManager(tmp_path)
    session_id = "door-check-warning"
    manager.start_session(session_id, SCENARIO_ID)
    manager.process_action(session_id, hallway_action(session_id, "assess_scene", 1))
    manager.process_action(session_id, hallway_action(session_id, "scan_hallway", 2))

    result = manager.process_action(session_id, hallway_action(session_id, "open_exit_door", 3))

    assert result.update.validation_result.status == "warning"
    assert result.update.validation_result.warnings[0].code == "exit_door_check_not_recorded"
    assert result.update.scenario_state.state["exit_door_open"] is False


def test_guidance_before_monitoring_environment_warns_without_transition(
    tmp_path: Path,
) -> None:
    manager = SessionManager(tmp_path)
    session_id = "monitor-warning"
    manager.start_session(session_id, SCENARIO_ID)
    actions = [
        "assess_scene",
        "scan_hallway",
        "confirm_ppe",
        "request_backup",
        "communicate_status",
        "check_visibility",
        "identify_secondary_exit",
        "move_obstacle",
        "check_exit_door",
        "open_exit_door",
        "guide_occupant_to_exit",
    ]

    result = None
    for sequence_number, action in enumerate(actions, start=1):
        result = manager.process_action(session_id, hallway_action(session_id, action, sequence_number))

    assert result is not None
    assert result.update.validation_result.status == "warning"
    assert result.update.validation_result.warnings[0].code == "environment_not_monitored"
    assert result.update.scenario_state.state["phase"] == "scene_assessed"
    assert result.update.scenario_state.state["occupant_guided"] is False


def test_blocked_exit_hallway_engine_is_deterministic() -> None:
    scenario = load_scenario(SCENARIO_ID)

    def run() -> dict[str, object]:
        engine = ScenarioEngine(scenario)
        state = engine.initial_state()
        for action in HAPPY_PATH:
            state = engine.preview_action(state, action).state
        return state

    assert run() == run()


def test_blocked_exit_hallway_review_summary_includes_hallway_cues(
    tmp_path: Path,
) -> None:
    manager = SessionManager(tmp_path)
    session_id = "blocked-exit-review"
    manager.start_session(session_id, SCENARIO_ID)
    for sequence_number, action in enumerate(HAPPY_PATH, start=1):
        manager.process_action(session_id, hallway_action(session_id, action, sequence_number))

    summary = generate_review_summary(tmp_path / f"{session_id}.jsonl")
    rendered = format_review_summary(summary)

    assert summary["scenario_id"] == SCENARIO_ID
    assert summary["environment_review"]["room_cues"]["area_label"] == "Hallway"
    assert summary["environment_review"]["room_cues"]["occupant_guided"] is True
    assert "Hallway cues:" in rendered
    assert "Collapsed bookshelf:" in rendered
    assert "Hallway exit door:" in rendered
    assert "Hallway smoke/haze cue:" in rendered
