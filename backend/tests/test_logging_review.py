import json
from pathlib import Path

from backend.app.logging.jsonl_logger import JsonlSessionLogger
from backend.app.logging.review_summary import generate_review_summary
from backend.app.orchestrator.session_manager import SessionManager
from backend.tests.conftest import action_message


def test_jsonl_logger_writes_valid_json_lines(tmp_path: Path) -> None:
    logger = JsonlSessionLogger(tmp_path)
    path = logger.append("log-test", {"event_type": "one", "sequence_number": 1})
    logger.append("log-test", {"event_type": "two", "sequence_number": 2})

    lines = path.read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["event_type"] for line in lines] == ["one", "two"]


def test_review_summary_reports_actions_findings_and_end_state(tmp_path: Path) -> None:
    manager = SessionManager(tmp_path)
    session_id = "review-test"
    manager.start_session(session_id)
    actions = ["confirm_ppe", "assess_scene", "stop_scenario"]
    for sequence_number, action in enumerate(actions, start=1):
        manager.process_action(session_id, action_message(session_id, action, sequence_number))

    summary = generate_review_summary(tmp_path / f"{session_id}.jsonl")

    assert summary["session_id"] == session_id
    assert summary["actions_taken"] == actions
    assert summary["warnings"]
    assert summary["end_condition_reached"] is True
    assert summary["final_state"]["scenario_outcome"] == "stopped"
    chair = summary["environment_review"]["wooden_chair_poc"]
    assert chair["blocked_path"] is True
    assert chair["moved"] is False
    assert chair["physics_enabled"] is False
    assert "Mass alone" in chair["gravity_note"]
    door = summary["environment_review"]["entry_door_poc"]
    assert door["open"] is False
    assert door["blocked_path"] is True
    assert door["locked"] is False
    assert door["door_type"] == "hinged_wooden_door_preview"
