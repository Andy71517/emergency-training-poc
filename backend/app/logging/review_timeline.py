"""Action timeline, state-change summaries, and progress stories."""

from typing import Any


STATE_CHANGE_LABELS = {
    "scene_assessed": "Scene assessment recorded",
    "room_scanned": "Room cues recorded",
    "hallway_scanned": "Hallway cues recorded",
    "ppe_confirmed": "PPE confirmation recorded",
    "backup_requested": "Backup request recorded",
    "door_checked": "Entry door checked",
    "exit_door_checked": "Exit door checked",
    "status_communicated": "Status communication recorded",
    "environment_monitored": "Environmental monitoring recorded",
    "path_blocked": "Room-entry path blockage changed",
    "primary_exit_blocked": "Primary-exit blockage changed",
    "door_open": "Entry door state changed",
    "exit_door_open": "Exit door state changed",
    "exit_path_clear": "Exit path state changed",
    "visibility_checked": "Visibility cue checked",
    "secondary_exit_identified": "Secondary exit identified",
    "exit_route_selected": "Exit route selected",
    "occupant_visible": "Occupant visibility changed",
    "occupant_located": "Occupant recorded as located",
    "occupant_removed": "Occupant recorded as removed",
    "occupant_guided": "Occupant recorded as guided to the exit",
    "scenario_outcome": "Scenario outcome changed",
}


def friendly_state(value: Any) -> str:
    if value is None:
        return "unknown"
    return str(value).replace("_", " ")


def summarize_state_changes(
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
) -> list[str]:
    """Describe meaningful top-level scenario changes without exposing field names."""

    if not isinstance(before, dict) or not isinstance(after, dict):
        return []
    changes: list[str] = []
    before_phase = before.get("phase")
    after_phase = after.get("phase")
    if before_phase != after_phase:
        changes.append(
            f"Progress moved from {friendly_state(before_phase)} to {friendly_state(after_phase)}."
        )
    for field, label in STATE_CHANGE_LABELS.items():
        if field == "scenario_outcome" or before.get(field) == after.get(field):
            continue
        new_value = after.get(field)
        if isinstance(new_value, bool):
            changes.append(f"{label}: {'yes' if new_value else 'no'}.")
        elif new_value is not None:
            changes.append(f"{label}: {friendly_state(new_value)}.")
    if before.get("scenario_outcome") != after.get("scenario_outcome"):
        changes.append(
            f"Scenario outcome: {friendly_state(after.get('scenario_outcome'))}."
        )
    return changes


def action_result_summary(item: dict[str, Any]) -> str:
    """Give each recorded action a short, audience-friendly outcome."""

    status = item.get("validation_status")
    changes = item.get("state_changes") or []
    if status == "error":
        return "The action was not accepted; scenario state stayed at the required earlier step."
    if status == "warning":
        if changes:
            return "The action was recorded, but the POC rules added a review point."
        return "The action produced a review point without advancing the scenario."
    if changes:
        return "The action was accepted and updated the scenario state."
    return "The action was accepted; no visible progress marker changed."


def action_progress_stories(action_timeline: list[dict[str, Any]]) -> list[str]:
    """Explain repeated attempts as plain-English state progress, not raw fields."""

    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in action_timeline:
        grouped.setdefault(str(item.get("action_type", "action")), []).append(item)

    stories: list[str] = []
    for action_type, attempts in grouped.items():
        if len(attempts) < 2:
            continue
        earlier_blocked = sum(
            item.get("validation_status") in {"warning", "error"} for item in attempts[:-1]
        )
        if not earlier_blocked:
            continue
        label = action_type.replace("_", " ").capitalize()
        if attempts[-1].get("validation_status") == "ok":
            stories.append(
                f"{label} was tried {len(attempts)} times. "
                f"{earlier_blocked} earlier attempt{' produced' if earlier_blocked == 1 else 's produced'} "
                "a review finding before the required scenario state changed; "
                "the later attempt was then accepted."
            )
        else:
            stories.append(
                f"{label} was tried {len(attempts)} times but remained unavailable because "
                "the required scenario state was still incomplete."
            )
    return stories
