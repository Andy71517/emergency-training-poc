import scripts.run_menu_demo as menu_demo
from scripts.run_menu_demo import (
    DEMO_DEFINITIONS,
    format_menu_review,
    friendly_label,
    parse_action_list,
    render_session_comparison,
    replay_or_saved_review,
    signed_difference,
    wants_yes,
)


def test_menu_includes_four_requested_deterministic_demo_paths() -> None:
    assert [definition.scenario_id for definition in DEMO_DEFINITIONS] == [
        "smoke_inhalation_room_v0",
        "smoke_inhalation_room_v0",
        "blocked_exit_hallway_v0",
        "blocked_exit_hallway_v0",
    ]
    assert all(definition.actions for definition in DEMO_DEFINITIONS)


def test_custom_action_parser_ignores_empty_entries() -> None:
    assert parse_action_list(" assess_scene, , stop_scenario ") == [
        "assess_scene",
        "stop_scenario",
    ]


def test_menu_review_uses_plain_english_instead_of_internal_names() -> None:
    summary = {
        "scenario_id": "smoke_inhalation_room_v0",
        "review_headline": "The run reached the toy end condition.",
        "end_condition_reached": True,
        "action_timeline": [
            {"action_type": "assess_scene", "validation_status": "ok"},
            {"action_type": "enter_room", "validation_status": "warning"},
        ],
        "environment_review": {"room_cues": {"room_scanned": True}},
        "warnings": [{"code": "internal_code", "message": "Check the visible cue first."}],
        "errors": [],
    }

    concise = format_menu_review(summary, replay_result={"verified": True})
    rendered = format_menu_review(
        summary,
        replay_result={"verified": True},
        show_action_details=True,
    )

    assert "Full sequence hidden" in concise
    assert "assess_scene" not in concise
    assert "Assess scene, Enter room" in rendered
    assert "Enter room: Review suggested" in rendered
    assert "Check the visible cue first." in rendered
    assert "assess_scene" not in rendered
    assert "internal_code" not in rendered
    assert friendly_label("blocked_exit_hallway_v0") == "Blocked exit hallway"


def test_yes_no_prompt_defaults_support_presentable_run_all_flow() -> None:
    assert wants_yes("", default=True)
    assert not wants_yes("", default=False)
    assert wants_yes("yes", default=False)
    assert not wants_yes("n", default=True)


def test_session_comparison_is_plain_english_and_not_a_score() -> None:
    first = {
        "scenario_id": "smoke_inhalation_room_v0",
        "scenario_outcome": "completed",
        "end_condition_reached": True,
        "total_actions": 13,
        "warnings": [],
        "errors": [],
    }
    second = {
        "scenario_id": "smoke_inhalation_room_v0",
        "scenario_outcome": "stopped",
        "end_condition_reached": True,
        "total_actions": 17,
        "warnings": [{"code": "warning"}],
        "errors": [{"code": "error"}],
    }

    rendered = render_session_comparison(
        first,
        second,
        first_label="happy.jsonl",
        second_label="warning.jsonl",
    )

    assert "Session comparison" in rendered
    assert "warnings +1, errors +1" in rendered
    assert "not clinical validation" in rendered
    assert signed_difference(0) == "0"


def test_old_replay_mismatch_falls_back_to_saved_review(monkeypatch, tmp_path) -> None:
    log_path = tmp_path / "older-session.jsonl"
    log_path.write_text("{}\n", encoding="utf-8")
    summary = {
        "scenario_id": "smoke_inhalation_room_v0",
        "review_headline": "Saved review remains readable.",
        "end_condition_reached": False,
        "action_timeline": [],
        "environment_review": {},
        "warnings": [],
        "errors": [],
    }
    output: list[str] = []
    monkeypatch.setattr(menu_demo, "replay", lambda _path: (_ for _ in ()).throw(ValueError("Replay mismatch at sequence 1")))
    monkeypatch.setattr(menu_demo, "generate_review_summary", lambda _path: summary)

    result = replay_or_saved_review(log_path, output.append)

    assert result == {"verified": False, "saved_review_available": True}
    assert "older log cannot be strictly replayed" in output[0]
    assert "DEMO REVIEW" in output[1]
