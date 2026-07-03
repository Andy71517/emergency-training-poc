from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.app.main import create_app
from backend.app.models.messages import TraineeActionMessage
from backend.app.orchestrator.session_manager import SessionInputError, SessionManager
from backend.tests.conftest import action_message


def test_session_manager_rejects_path_like_session_ids(tmp_path: Path) -> None:
    manager = SessionManager(tmp_path)

    with pytest.raises(SessionInputError, match="session_id"):
        manager.start_session("../bad")

    assert "../bad" not in manager.sessions
    assert not list(tmp_path.glob("*.jsonl"))


def test_session_manager_rejects_path_like_scenario_ids(tmp_path: Path) -> None:
    manager = SessionManager(tmp_path)

    with pytest.raises(SessionInputError, match="scenario_id"):
        manager.start_session("safe-session", "../scenario")

    assert "safe-session" not in manager.sessions


def test_message_model_rejects_unsafe_event_id() -> None:
    raw_message = action_message("security-test", "assess_scene", 1).model_dump(mode="json")
    raw_message["trainee_action"]["event_id"] = "../event"
    raw_message["correlation_event_id"] = "../event"

    with pytest.raises(ValidationError, match="event_id"):
        TraineeActionMessage.model_validate(raw_message)


def test_message_model_rejects_oversized_payload_string() -> None:
    raw_message = action_message("security-test", "assess_scene", 1).model_dump(mode="json")
    raw_message["trainee_action"]["payload"] = {"note": "x" * 501}

    with pytest.raises(ValidationError, match="payload.note"):
        TraineeActionMessage.model_validate(raw_message)


def test_message_model_accepts_small_json_payload() -> None:
    raw_message = action_message("security-test", "assess_scene", 1).model_dump(mode="json")
    raw_message["trainee_action"]["payload"] = {
        "note": "stubbed input only",
        "confidence": 0.5,
        "flags": ["manual", "demo"],
    }

    message = TraineeActionMessage.model_validate(raw_message)

    assert message.trainee_action.payload["note"] == "stubbed input only"


def test_websocket_rejects_unsafe_session_id(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))

    with client.websocket_connect("/ws/sessions/bad.session") as websocket:
        websocket.send_json({"message_type": "start_session"})
        response = websocket.receive_json()

    assert response["message_type"] == "error"
    assert response["code"] == "invalid_session_id"
    assert "session_id" in response["message"]


def test_session_manager_limits_active_sessions(tmp_path: Path) -> None:
    manager = SessionManager(tmp_path, max_active_sessions=1)
    manager.start_session("session-one")

    with pytest.raises(SessionInputError, match="Active session limit"):
        manager.start_session("session-two")

    assert manager.active_session_count() == 1


def test_ended_sessions_do_not_count_against_active_session_limit(tmp_path: Path) -> None:
    manager = SessionManager(tmp_path, max_active_sessions=1)
    manager.start_session("session-one")
    actions = [
        "assess_scene",
        "confirm_ppe",
        "request_backup",
        "move_obstacle",
        "open_door",
        "check_visibility",
        "enter_room",
        "remove_occupant",
    ]
    for sequence_number, action in enumerate(actions, start=1):
        manager.process_action("session-one", action_message("session-one", action, sequence_number))

    manager.start_session("session-two")

    assert manager.active_session_count() == 1


def test_session_manager_limits_actions_per_session(tmp_path: Path) -> None:
    manager = SessionManager(tmp_path, max_actions_per_session=1)
    manager.start_session("limited-session")
    manager.process_action("limited-session", action_message("limited-session", "assess_scene", 1))

    with pytest.raises(SessionInputError, match="Action limit"):
        manager.process_action("limited-session", action_message("limited-session", "confirm_ppe", 2))


def test_websocket_returns_specific_sequence_error_code(tmp_path: Path) -> None:
    session_id = "sequence-error-test"
    client = TestClient(create_app(tmp_path))

    with client.websocket_connect(f"/ws/sessions/{session_id}") as websocket:
        websocket.send_json({"message_type": "start_session"})
        websocket.receive_json()
        websocket.send_json(action_message(session_id, "confirm_ppe", 2).model_dump(mode="json"))
        response = websocket.receive_json()

    assert response["message_type"] == "error"
    assert response["code"] == "sequence_number_out_of_order"
    assert "Expected sequence_number 1" in response["message"]
