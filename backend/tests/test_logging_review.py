import json
from pathlib import Path

from backend.app.logging.jsonl_logger import JsonlSessionLogger
from backend.app.logging.review_summary import format_review_summary, generate_review_summary
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
    assert summary["review_headline"]
    assert summary["actions_taken"] == actions
    assert summary["total_actions"] == 3
    assert summary["validation_counts"]["warning"] >= 1
    assert summary["action_timeline"][0]["action_type"] == "confirm_ppe"
    assert summary["action_timeline"][0]["validation_status"] == "warning"
    assert summary["warnings"]
    assert summary["end_condition_reached"] is True
    assert summary["scenario_outcome"] == "stopped"
    assert summary["final_phase"] == "stopped"
    assert summary["final_state"]["scenario_outcome"] == "stopped"
    assert summary["key_observations"]
    assert summary["reviewer_takeaways"]
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
    visibility = summary["environment_review"]["smoke_visibility_cue_poc"]
    assert visibility["observed"] is False
    assert visibility["visibility_level"] == "low"


def test_review_summary_formats_human_readable_debrief(tmp_path: Path) -> None:
    manager = SessionManager(tmp_path)
    session_id = "review-format-test"
    manager.start_session(session_id)
    actions = ["assess_scene", "stop_scenario"]
    for sequence_number, action in enumerate(actions, start=1):
        manager.process_action(session_id, action_message(session_id, action, sequence_number))

    summary = generate_review_summary(tmp_path / f"{session_id}.jsonl")
    rendered = format_review_summary(
        summary,
        replay_result={"verified": True, "events_replayed": 2},
        label="demo review",
        log_path=tmp_path / f"{session_id}.jsonl",
        physics_preview="both",
    )

    assert "Post-scenario review" in rendered
    assert "Session: demo review" in rendered
    assert "What happened:" in rendered
    assert "Review snapshot:" in rendered
    assert "Action timeline:" in rendered
    assert "1. assess_scene -> ok" in rendered
    assert "Environment cues:" in rendered
    assert "Smoke/visibility cue:" in rendered
    assert "Key observations:" in rendered
    assert "Reviewer takeaways:" in rendered
    assert "Replay verified: yes" in rendered
