from scripts.unreal_display_preview import build_display_state, render_debug_panel


def test_unreal_display_state_maps_chair_and_door() -> None:
    display_state = build_display_state(
        session_id="demo-happy",
        scenario_id="smoke_inhalation_room_v0",
        phase="room_entered",
        validation_status="ok",
        warnings=[],
        errors=[],
        environment_review={
            "wooden_chair_poc": {
                "label": "Wooden chair",
                "location": "clear_of_entry_path",
                "blocked_path": False,
                "moved": True,
                "physics_enabled": False,
            },
            "entry_door_poc": {
                "label": "Entry door",
                "open": True,
                "open_state": "open",
                "blocked_path": False,
                "locked": False,
                "door_type": "hinged_wooden_door_preview",
            },
            "smoke_visibility_cue_poc": {
                "label": "Smoke/visibility cue",
                "observed": True,
                "visibility_level": "checked_low_visibility",
                "blocked_path": False,
                "physics_enabled": False,
            },
        },
    )

    assert display_state["objects"] == [
        {
            "object_id": "wooden_chair_poc",
            "label": "Wooden chair",
            "display": "moved aside",
            "blocks_path": False,
            "metadata": {"location": "clear_of_entry_path", "physics_enabled": False},
        },
        {
            "object_id": "entry_door_poc",
            "label": "Entry door",
            "display": "open",
            "blocks_path": False,
            "metadata": {"locked": False, "door_type": "hinged_wooden_door_preview"},
        },
        {
            "object_id": "smoke_visibility_cue_poc",
            "label": "Smoke/visibility cue",
            "display": "checked",
            "blocks_path": False,
            "metadata": {"visibility_level": "checked_low_visibility", "physics_enabled": False},
        },
    ]


def test_unreal_debug_panel_renders_warnings_and_errors() -> None:
    display_state = build_display_state(
        session_id="demo-warning",
        scenario_id="smoke_inhalation_room_v0",
        phase="scene_assessed",
        validation_status="warning",
        warnings=[{"code": "entry_door_still_closed", "message": "Open the door before entering."}],
        errors=[{"code": "entry_prerequisites_missing", "message": "Setup flags are incomplete."}],
        environment_review={
            "wooden_chair_poc": {
                "label": "Wooden chair",
                "blocked_path": False,
                "moved": True,
            },
            "entry_door_poc": {
                "label": "Entry door",
                "open_state": "closed",
                "blocked_path": True,
                "locked": False,
                "door_type": "hinged_wooden_door_preview",
            },
            "smoke_visibility_cue_poc": {
                "label": "Smoke/visibility cue",
                "observed": False,
                "visibility_level": "low",
                "blocked_path": False,
            },
        },
    )

    panel = render_debug_panel(display_state)

    assert "Unreal debug display preview" in panel
    assert "Wooden chair: moved aside (not blocking path)" in panel
    assert "Entry door: closed (blocking path)" in panel
    assert "Smoke/visibility cue: unchecked (not blocking path)" in panel
    assert "entry_door_still_closed: Open the door before entering." in panel
    assert "entry_prerequisites_missing: Setup flags are incomplete." in panel
    assert "Unreal must not own scenario logic." in panel


def test_unreal_display_handles_missing_objects() -> None:
    display_state = build_display_state(
        session_id="demo-empty",
        scenario_id="smoke_inhalation_room_v0",
        phase="awaiting_assessment",
        validation_status="ok",
        warnings=[],
        errors=[],
        environment_review={},
    )

    assert display_state["objects"] == []
    assert "no environment objects found" in render_debug_panel(display_state)
