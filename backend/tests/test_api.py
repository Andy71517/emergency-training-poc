from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.tests.conftest import action_message


def test_health_endpoint(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))
    assert client.get("/health").json()["status"] == "ok"


def test_websocket_accepts_action_and_returns_state_update(tmp_path: Path) -> None:
    session_id = "websocket-test"
    client = TestClient(create_app(tmp_path))

    with client.websocket_connect(f"/ws/sessions/{session_id}") as websocket:
        websocket.send_json({"message_type": "start_session"})
        started = websocket.receive_json()
        websocket.send_json(action_message(session_id, "assess_scene", 1).model_dump(mode="json"))
        update = websocket.receive_json()

    assert started["message_type"] == "session_started"
    assert update["message_type"] == "scenario_state_update"
    assert update["scenario_state"]["state"]["scene_assessed"] is True
    assert update["validation_result"]["status"] == "ok"


def test_websocket_can_start_blocked_exit_hallway_scenario(tmp_path: Path) -> None:
    session_id = "websocket-hallway-test"
    scenario_id = "blocked_exit_hallway_v0"
    client = TestClient(create_app(tmp_path))

    with client.websocket_connect(f"/ws/sessions/{session_id}") as websocket:
        websocket.send_json({"message_type": "start_session", "scenario_id": scenario_id})
        started = websocket.receive_json()
        websocket.send_json(
            action_message(
                session_id,
                "assess_scene",
                1,
                scenario_id=scenario_id,
            ).model_dump(mode="json")
        )
        update = websocket.receive_json()

    assert started["message_type"] == "session_started"
    assert started["scenario_id"] == scenario_id
    assert update["message_type"] == "scenario_state_update"
    assert update["scenario_state"]["state"]["scene_assessed"] is True
    assert update["scenario_state"]["state"]["primary_exit_blocked"] is True
    assert update["validation_result"]["status"] == "ok"
