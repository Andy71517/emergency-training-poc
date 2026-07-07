import json
from pathlib import Path

from scripts.run_local_demo import (
    DemoSession,
    build_demo_sessions,
    chair_previews,
    is_backend_healthy,
    render_chair_preview,
    render_review_report,
    ws_url_from_http,
)


class FakeHealthResponse:
    status = 200

    def __enter__(self) -> "FakeHealthResponse":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps({"status": "ok"}).encode("utf-8")


def test_demo_session_ids_are_safe_and_unique() -> None:
    sessions = build_demo_sessions("Demo Run", "20260701-120000")

    assert [session.session_id for session in sessions] == [
        "demo-run-happy-20260701-120000",
        "demo-run-warning-error-20260701-120000",
    ]
    assert sessions[0].log_path == Path("logs/sessions/demo-run-happy-20260701-120000.jsonl")


def test_ws_url_derives_from_http_url() -> None:
    assert ws_url_from_http("http://127.0.0.1:8765") == "ws://127.0.0.1:8765"
    assert ws_url_from_http("https://example.invalid:9443") == "wss://example.invalid:9443"


def test_backend_health_check_accepts_ok_response(monkeypatch) -> None:
    def fake_urlopen(url: str, timeout: float) -> FakeHealthResponse:
        assert url == "http://127.0.0.1:8765/health"
        assert timeout == 1.0
        return FakeHealthResponse()

    monkeypatch.setattr("scripts.run_local_demo.urlopen", fake_urlopen)

    assert is_backend_healthy("http://127.0.0.1:8765") is True


def test_backend_health_check_handles_failures(monkeypatch) -> None:
    def fake_urlopen(url: str, timeout: float) -> FakeHealthResponse:
        raise OSError("offline")

    monkeypatch.setattr("scripts.run_local_demo.urlopen", fake_urlopen)

    assert is_backend_healthy("http://127.0.0.1:8765") is False


def test_chair_preview_supports_disabled_enabled_and_both() -> None:
    disabled = chair_previews("disabled")
    enabled = chair_previews("enabled")
    both = chair_previews("both")

    assert disabled[0]["physics_enabled"] is False
    assert enabled[0]["physics_enabled"] is True
    assert [preview["physics_enabled"] for preview in both] == [False, True]
    rendered = render_chair_preview(both)
    assert "Wooden chair" in rendered
    assert "No mesh is generated or loaded." in rendered
    assert "future physics candidate preview" in rendered
    assert "Mass alone does not cover gravity" in rendered


def test_review_report_formats_summary_and_replay_result() -> None:
    session = DemoSession(
        label="warning/error path",
        session_id="demo-warning-error-test",
        actions=["confirm_ppe"],
        log_path=Path("logs/sessions/demo-warning-error-test.jsonl"),
    )
    summary = {
        "actions_taken": ["confirm_ppe"],
        "final_state": {"phase": "stopped"},
        "end_condition_reached": True,
        "environment_review": {
            "room_cues": {
                "room_scanned": True,
                "door_checked": False,
                "status_communicated": True,
                "environment_monitored": False,
                "exit_path_clear": True,
                "occupant_visible": False,
                "occupant_located": False,
                "smoke_density": "moderate_preview_observed",
                "visibility_level": "checked_low_visibility",
                "air_quality_warning": "present_preview",
            },
            "wooden_chair_poc": {
                "blocked_path": False,
                "moved": True,
                "physics_enabled": False,
                "gravity_note": "Mass alone does not simulate gravity.",
            },
            "entry_door_poc": {
                "open": True,
                "blocked_path": False,
                "locked": False,
                "door_type": "hinged_wooden_door_preview",
            },
            "smoke_visibility_cue_poc": {
                "label": "Smoke/visibility cue",
                "observed": False,
                "visibility_level": "low",
                "blocked_path": False,
                "physics_enabled": False,
                "cue_note": "POC cue only.",
            },
        },
        "warnings": [{"code": "assessment_not_recorded", "message": "Scene assessment missing."}],
        "errors": [{"code": "entry_prerequisites_missing", "message": "Setup flags missing."}],
    }
    replay_result = {"verified": True, "events_replayed": 4}

    report = render_review_report(session=session, summary=summary, replay_result=replay_result)

    assert "Post-scenario review" in report
    assert "Session: warning/error path" in report
    assert "Actions reviewed: 1" in report
    assert "Replay verified: yes" in report
    assert "Room cues:" in report
    assert "environment monitored: no" in report
    assert "Wooden chair:" in report
    assert "moved during scenario: yes" in report
    assert "Entry door:" in report
    assert "open at end: yes" in report
    assert "Smoke/visibility cue:" in report
    assert "checked during scenario: no" in report
    assert "assessment_not_recorded: Scene assessment missing." in report
    assert "Reviewer takeaways:" in report


def test_demo_does_not_require_generated_assets() -> None:
    generated_files = {
        path.name
        for path in Path("assets/generated").iterdir()
        if path.is_file()
    }

    assert generated_files <= {"README.md", ".gitkeep"}
