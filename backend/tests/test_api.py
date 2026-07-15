from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.tests.conftest import action_message


def test_health_endpoint(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))
    assert client.get("/health").json()["status"] == "ok"


def test_demo_paths_are_backend_owned_and_presentation_safe(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))

    response = client.get("/api/demo/paths")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["paths"]) == 4
    assert payload["paths"][0]["demo_id"] == "smoke-room-happy"
    assert payload["paths"][0]["actions"][0] == "assess_scene"
    assert "not clinical validation" in payload["disclaimer"]


def test_demo_review_reads_the_backend_session_log(tmp_path: Path) -> None:
    session_id = "web-review-test"
    client = TestClient(create_app(tmp_path))

    with client.websocket_connect(f"/ws/sessions/{session_id}") as websocket:
        websocket.send_json({"message_type": "start_session"})
        websocket.receive_json()
        websocket.send_json(action_message(session_id, "assess_scene", 1).model_dump(mode="json"))
        websocket.receive_json()

    response = client.get(f"/api/demo/reviews/{session_id}")

    assert response.status_code == 200
    assert response.json()["review"]["actions_taken"] == ["assess_scene"]
    assert response.json()["log_name"] == f"{session_id}.jsonl"


def test_demo_review_rejects_unsafe_or_missing_session_ids(tmp_path: Path) -> None:
    client = TestClient(create_app(tmp_path))

    assert client.get("/api/demo/reviews/bad.session").status_code == 400
    assert client.get("/api/demo/reviews/not-found").status_code == 404


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
