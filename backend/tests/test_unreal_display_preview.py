import json
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.unreal_display_preview import build_display_state, render_debug_panel
from scripts.write_unreal_debug_text import debug_text_from_display_state, write_debug_text


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

    assert display_state["schema_version"] == "0.1.0"
    assert display_state["display_mode"] == "text_debug"
    assert display_state["status_line"] == "room_entered / ok / no findings"
    assert display_state["objects"] == [
        {
            "object_id": "wooden_chair_poc",
            "label": "Wooden chair",
            "display": "moved aside",
            "blocks_path": False,
            "alert_level": "normal",
            "metadata": {"location": "clear_of_entry_path", "physics_enabled": False},
        },
        {
            "object_id": "entry_door_poc",
            "label": "Entry door",
            "display": "open",
            "blocks_path": False,
            "alert_level": "normal",
            "metadata": {"locked": False, "door_type": "hinged_wooden_door_preview"},
        },
        {
            "object_id": "smoke_visibility_cue_poc",
            "label": "Smoke/visibility cue",
            "display": "checked",
            "blocks_path": False,
            "alert_level": "normal",
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
    assert "Status: scene_assessed / warning / 1 error(s)" in panel
    assert "[normal] Wooden chair: moved aside (not blocking path)" in panel
    assert "[attention] Entry door: closed (blocking path)" in panel
    assert "[attention] Smoke/visibility cue: unchecked (not blocking path)" in panel
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


def test_unreal_display_maps_generic_hallway_objects() -> None:
    display_state = build_display_state(
        session_id="demo-hallway",
        scenario_id="blocked_exit_hallway_v0",
        phase="scene_assessed",
        validation_status="warning",
        warnings=[
            {
                "code": "environment_not_monitored",
                "message": "The ongoing hallway environment cue has not been checked before guidance.",
            }
        ],
        errors=[],
        environment_review={
            "other_environment_objects": {
                "collapsed_bookshelf_poc": {
                    "label": "Collapsed bookshelf",
                    "object_type": "obstacle",
                    "location": "clear_of_primary_exit_path",
                    "blocked_path": False,
                    "moved": True,
                    "physics_enabled": False,
                }
            }
        },
    )

    assert display_state["objects"] == [
        {
            "object_id": "collapsed_bookshelf_poc",
            "label": "Collapsed bookshelf",
            "display": "moved aside",
            "blocks_path": False,
            "alert_level": "normal",
            "metadata": {
                "object_type": "obstacle",
                "location": "clear_of_primary_exit_path",
                "physics_enabled": False,
            },
        }
    ]
    assert "[normal] Collapsed bookshelf: moved aside" in render_debug_panel(display_state)


def test_checked_in_display_examples_follow_schema() -> None:
    schema = json.loads(Path("unreal/contract/debug-display-state.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)

    for path in Path("unreal/contract/examples").glob("*display_state*.json"):
        validator.validate(json.loads(path.read_text(encoding="utf-8")))


def test_unreal_starter_samples_match_contract_examples() -> None:
    pairs = [
        (
            Path("unreal/contract/examples/display_state.example.json"),
            Path("unreal/EmergencyTrainingClient/Data/display_state.sample.json"),
        ),
        (
            Path("unreal/contract/examples/warning_display_state.example.json"),
            Path("unreal/EmergencyTrainingClient/Data/warning_display_state.sample.json"),
        ),
        (
            Path("unreal/contract/examples/hallway_display_state.example.json"),
            Path("unreal/EmergencyTrainingClient/Data/hallway_display_state.sample.json"),
        ),
    ]

    for source, starter_sample in pairs:
        assert json.loads(starter_sample.read_text(encoding="utf-8")) == json.loads(
            source.read_text(encoding="utf-8")
        )


def test_unreal_debug_text_bridge_writes_sample_text(tmp_path: Path) -> None:
    source = Path("unreal/EmergencyTrainingClient/Data/hallway_display_state.sample.json")
    output = tmp_path / "hallway_debug_panel.sample.txt"

    debug_text = write_debug_text(source, output)

    assert output.read_text(encoding="utf-8") == debug_text + "\n"
    assert "Session: demo-hallway" in debug_text
    assert "[attention] Ongoing hallway monitor: unchecked" in debug_text
    assert "Unreal must not own scenario logic." in debug_text


def test_checked_in_unreal_debug_text_matches_json_bridge() -> None:
    source = Path("unreal/EmergencyTrainingClient/Data/hallway_display_state.sample.json")
    checked_in_text = Path("unreal/EmergencyTrainingClient/Data/hallway_debug_panel.sample.txt")

    assert checked_in_text.read_text(encoding="utf-8").strip() == debug_text_from_display_state(
        source
    )
