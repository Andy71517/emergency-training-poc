"""Generate a concise review from one ordered POC session log."""

import json
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    with Path(path).open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if line.strip():
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError as error:
                    raise ValueError(f"Invalid JSON on line {line_number}") from error
    return entries


def generate_review_summary(path: Path) -> dict[str, Any]:
    entries = load_jsonl(path)
    if not entries:
        raise ValueError("Session log is empty")

    actions: list[str] = []
    warnings: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    final_state: dict[str, Any] = {}
    end_reached = False

    for entry in entries:
        inbound = entry.get("inbound_message") or {}
        event = inbound.get("trainee_action") or {}
        if event.get("action_type"):
            actions.append(event["action_type"])
        validation = entry.get("validation_result") or {}
        warnings.extend(validation.get("warnings", []))
        errors.extend(validation.get("errors", []))
        if entry.get("state_snapshot") is not None:
            final_state = entry["state_snapshot"]
        end_reached = end_reached or entry.get("event_type") == "scenario_ended"

    return {
        "session_id": entries[0].get("session_id"),
        "scenario_id": entries[0].get("scenario_id"),
        "final_state": final_state,
        "environment_review": environment_review(final_state),
        "actions_taken": actions,
        "warnings": warnings,
        "errors": errors,
        "end_condition_reached": end_reached,
    }


def environment_review(state: dict[str, Any]) -> dict[str, Any]:
    objects = state.get("environment", {}).get("objects", {})
    chair = objects.get("wooden_chair_poc", {})
    door = objects.get("entry_door_poc", {})
    review: dict[str, Any] = {}
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
    return review
