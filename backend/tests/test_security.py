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
    assert response["code"] == "session_error"
    assert "session_id" in response["message"]

