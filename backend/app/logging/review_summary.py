"""Generate a readable review from one ordered POC session log.

This module is the public entry point for review generation. It delegates to
focused submodules for timeline analysis, environment snapshots, instructor
narratives, and text formatting.
"""

import json
from pathlib import Path
from typing import Any

from backend.app.logging.review_environment import environment_review
from backend.app.logging.review_formatter import (
    format_review_summary,
    yes_no,
)
from backend.app.logging.review_instructor import (
    build_instructor_review,
    key_observations,
    review_headline,
    reviewer_takeaways,
)
from backend.app.logging.review_timeline import (
    STATE_CHANGE_LABELS,
    action_progress_stories,
    action_result_summary,
    friendly_state,
    summarize_state_changes,
)


ACTION_DESCRIPTIONS = {
    "assess_scene": "Recorded an initial scene assessment.",
    "scan_room": "Checked the room and recorded the visible environmental cues.",
    "scan_hallway": "Checked the hallway and recorded the visible route cues.",
    "confirm_ppe": "Recorded the POC protective-equipment confirmation.",
    "request_backup": "Recorded a request for additional support.",
    "communicate_status": "Recorded a status update for the scenario timeline.",
    "check_door": "Checked the room-entry door condition.",
    "check_exit_door": "Checked the hallway exit-door condition.",
    "move_obstacle": "Attempted to clear the obstacle from the path.",
    "open_door": "Attempted to open the room-entry door.",
    "open_exit_door": "Attempted to open the hallway exit door.",
    "check_visibility": "Recorded a check of the visibility cue.",
    "identify_secondary_exit": "Recorded a possible secondary exit route.",
    "monitor_environment": "Recorded an ongoing environmental check.",
    "enter_room": "Attempted to move the scenario into the room-entry stage.",
    "locate_occupant": "Attempted to record the occupant as located.",
    "remove_occupant": "Attempted to record the occupant as removed from the room.",
    "guide_occupant_to_exit": "Attempted to record the occupant as guided to the exit.",
    "reassess_scene": "Recorded another assessment of the current scene state.",
    "retreat": "Recorded a retreat from the current scenario position.",
    "stop_scenario": "Stopped the toy scenario and preserved its current state for review.",
}


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
    action_timeline: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    final_state: dict[str, Any] = {}
    end_reached = False
    validation_counts = {"ok": 0, "warning": 0, "error": 0}
    previous_action_state: dict[str, Any] | None = None

    for entry in entries:
        inbound = entry.get("inbound_message") or {}
        event = inbound.get("trainee_action") or {}
        validation = entry.get("validation_result") or {}
        state_snapshot = entry.get("state_snapshot")
        if event.get("action_type"):
            actions.append(event["action_type"])
            status = validation.get("status", "unknown")
            if status in validation_counts:
                validation_counts[status] += 1
            timeline_item = {
                "sequence_number": entry.get("sequence_number"),
                "action_type": event["action_type"],
                "action_description": ACTION_DESCRIPTIONS.get(
                    event["action_type"],
                    "Recorded this action in the session timeline.",
                ),
                "validation_status": status,
                "warning_codes": [item.get("code") for item in validation.get("warnings", [])],
                "error_codes": [item.get("code") for item in validation.get("errors", [])],
                "finding_messages": [
                    item.get("message")
                    for item in validation.get("errors", []) + validation.get("warnings", [])
                    if item.get("message")
                ],
                "phase_before": (previous_action_state or {}).get("phase"),
                "phase_after": (state_snapshot or {}).get("phase"),
                "outcome_after": (state_snapshot or {}).get("scenario_outcome"),
                "state_changed": previous_action_state is None or previous_action_state != state_snapshot,
                "state_changes": summarize_state_changes(previous_action_state, state_snapshot),
            }
            timeline_item["result_summary"] = action_result_summary(timeline_item)
            action_timeline.append(timeline_item)
            if isinstance(state_snapshot, dict):
                previous_action_state = state_snapshot
        warnings.extend(validation.get("warnings", []))
        errors.extend(validation.get("errors", []))
        if state_snapshot is not None:
            final_state = state_snapshot
            if not event.get("action_type") and isinstance(state_snapshot, dict):
                previous_action_state = state_snapshot
        end_reached = end_reached or entry.get("event_type") == "scenario_ended"

    review = environment_review(final_state)
    headline = review_headline(
        validation_counts=validation_counts,
        end_reached=end_reached,
        final_phase=final_state.get("phase"),
    )
    progress_stories = action_progress_stories(action_timeline)
    instructor_review = build_instructor_review(
        action_count=len(actions),
        validation_counts=validation_counts,
        end_reached=end_reached,
        final_state=final_state,
        environment=review,
        progress_stories=progress_stories,
    )
    return {
        "session_id": entries[0].get("session_id"),
        "scenario_id": entries[0].get("scenario_id"),
        "review_headline": headline,
        "scenario_outcome": final_state.get("scenario_outcome"),
        "final_phase": final_state.get("phase"),
        "final_state": final_state,
        "environment_review": review,
        "actions_taken": actions,
        "action_timeline": action_timeline,
        "progress_stories": progress_stories,
        "instructor_review": instructor_review,
        "total_actions": len(actions),
        "validation_counts": validation_counts,
        "warnings": warnings,
        "errors": errors,
        "end_condition_reached": end_reached,
        "key_observations": key_observations(
            action_count=len(actions),
            validation_counts=validation_counts,
            end_reached=end_reached,
            environment=review,
        ),
        "reviewer_takeaways": reviewer_takeaways(warnings=warnings, errors=errors),
    }


# Re-export public symbols that external code may import from this module.
__all__ = [
    "ACTION_DESCRIPTIONS",
    "STATE_CHANGE_LABELS",
    "action_progress_stories",
    "action_result_summary",
    "build_instructor_review",
    "environment_review",
    "format_review_summary",
    "friendly_state",
    "generate_review_summary",
    "key_observations",
    "load_jsonl",
    "review_headline",
    "reviewer_takeaways",
    "summarize_state_changes",
    "yes_no",
]
