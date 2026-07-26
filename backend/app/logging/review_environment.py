"""Build the environment review snapshot from final scenario state."""

from typing import Any


def environment_review(state: dict[str, Any]) -> dict[str, Any]:
    environment = state.get("environment", {})
    objects = environment.get("objects", {})
    chair = objects.get("wooden_chair_poc", {})
    door = objects.get("entry_door_poc", {}) or first_object_by_type(objects, "door")
    visibility = objects.get("smoke_visibility_cue_poc", {}) or first_object_by_type(objects, "visibility_cue")
    other_objects = {
        object_id: object_state
        for object_id, object_state in objects.items()
        if object_id not in {"wooden_chair_poc", "entry_door_poc", "smoke_visibility_cue_poc"}
        and object_state is not door
        and object_state is not visibility
    }
    area_label = "Room" if "room_scanned" in state else "Hallway" if "hallway_scanned" in state else "Area"
    review: dict[str, Any] = {
        "room_cues": {
            "area_label": area_label,
            "room_scanned": bool(state.get("room_scanned") or state.get("hallway_scanned")),
            "door_checked": bool(state.get("door_checked") or state.get("exit_door_checked")),
            "status_communicated": bool(state.get("status_communicated")),
            "environment_monitored": bool(state.get("environment_monitored")),
            "occupant_visible": bool(state.get("occupant_visible") or state.get("occupant_guided")),
            "occupant_located": bool(state.get("occupant_located") or state.get("occupant_guided")),
            "occupant_removed": bool(state.get("occupant_removed")),
            "occupant_guided": bool(state.get("occupant_guided")),
            "exit_path_clear": bool(state.get("exit_path_clear") or environment.get("exit_path_clear")),
            "primary_exit_blocked": state.get("primary_exit_blocked"),
            "secondary_exit_identified": state.get("secondary_exit_identified"),
            "exit_route_selected": state.get("exit_route_selected"),
            "smoke_density": environment.get("smoke_density"),
            "visibility_level": environment.get("visibility_level"),
            "room_temperature": environment.get("room_temperature"),
            "air_quality_warning": environment.get("air_quality_warning"),
            "note": environment.get("notes"),
        }
    }
    if chair:
        review["wooden_chair_poc"] = {
            "label": chair.get("label", "Wooden chair"),
            "location": chair.get("location"),
            "blocked_path": bool(chair.get("blocks_path")),
            "moved": bool(chair.get("moved")),
            "physics_enabled": bool(chair.get("physics_enabled")),
            "physics_note": chair.get("physics_note"),
            "gravity_note": "Mass alone does not simulate gravity; real gravity needs a physics engine later.",
        }
    if door:
        review["entry_door_poc"] = {
            "label": door.get("label", "Entry door"),
            "location": door.get("location"),
            "open": door.get("open_state") == "open",
            "open_state": door.get("open_state"),
            "blocked_path": bool(door.get("blocks_path")),
            "locked": bool(door.get("locked")),
            "door_type": door.get("door_type"),
            "hinge_side": door.get("hinge_side"),
            "swing_direction": door.get("swing_direction"),
            "collision_enabled": bool(door.get("collision_enabled")),
            "mass_kg_estimate": door.get("mass_kg_estimate"),
            "force_preview": door.get("force_preview", {}),
            "physics_note": door.get("physics_note"),
        }
    if visibility:
        review["smoke_visibility_cue_poc"] = {
            "label": visibility.get("label", "Smoke/visibility cue"),
            "location": visibility.get("location"),
            "observed": bool(visibility.get("observed")),
            "visibility_level": visibility.get("visibility_level"),
            "blocked_path": bool(visibility.get("blocks_path")),
            "cue_note": visibility.get("cue_note"),
            "physics_enabled": bool(visibility.get("physics_enabled")),
            "physics_note": visibility.get("physics_note"),
        }
    if other_objects:
        review["other_environment_objects"] = {
            object_id: {
                "label": object_state.get("label", object_id),
                "object_type": object_state.get("object_type"),
                "location": object_state.get("location"),
                "blocked_path": bool(object_state.get("blocks_path")),
                "moved": object_state.get("moved"),
                "open_state": object_state.get("open_state"),
                "physics_enabled": bool(object_state.get("physics_enabled")),
                "physics_note": object_state.get("physics_note"),
            }
            for object_id, object_state in other_objects.items()
        }
    return review


def first_object_by_type(objects: dict[str, Any], object_type: str) -> dict[str, Any]:
    for object_state in objects.values():
        if object_state.get("object_type") == object_type:
            return object_state
    return {}
