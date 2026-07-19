"""Generate a readable review from one ordered POC session log."""

import json
from pathlib import Path
from typing import Any


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


def build_instructor_review(
    *,
    action_count: int,
    validation_counts: dict[str, int],
    end_reached: bool,
    final_state: dict[str, Any],
    environment: dict[str, Any],
    progress_stories: list[str],
) -> dict[str, Any]:
    """Create a final discussion aid from recorded POC evidence."""

    room_cues = environment.get("room_cues") or {}
    completed_cues = [
        label
        for field, label in (
            ("room_scanned", "area check"),
            ("door_checked", "door check"),
            ("status_communicated", "status communication"),
            ("environment_monitored", "environment monitoring"),
            ("exit_path_clear", "clear exit path"),
        )
        if room_cues.get(field)
    ]
    missing_cues = [
        label
        for field, label in (
            ("room_scanned", "area check"),
            ("door_checked", "door check"),
            ("status_communicated", "status communication"),
            ("environment_monitored", "environment monitoring"),
            ("exit_path_clear", "clear exit path"),
        )
        if not room_cues.get(field)
    ]
    finding_count = validation_counts.get("warning", 0) + validation_counts.get("error", 0)
    if finding_count:
        opening = (
            f"This session recorded {action_count} actions and {finding_count} POC review "
            f"finding{'s' if finding_count != 1 else ''}."
        )
    else:
        opening = f"This session recorded {action_count} actions with no POC review findings."

    evidence = [
        f"The scenario end condition was {'reached' if end_reached else 'not reached'}.",
        f"The final recorded outcome was {friendly_state(final_state.get('scenario_outcome'))}.",
        "Completed cues: " + (", ".join(completed_cues) if completed_cues else "none recorded") + ".",
        "Still missing: " + (", ".join(missing_cues) if missing_cues else "none") + ".",
    ]
    if progress_stories:
        evidence.append(
            f"The review identified {len(progress_stories)} blocked-or-flagged action "
            f"retr{'y' if len(progress_stories) == 1 else 'ies'} that can be discussed."
        )

    if progress_stories:
        discussion_prompt = (
            "Ask the trainee to explain what they noticed, what changed before the retry, "
            "and what they would want to review with an instructor."
        )
    elif missing_cues:
        discussion_prompt = (
            "Ask the trainee what they noticed, which recorded cues remained unresolved, "
            "and what they would want to review with an instructor."
        )
    else:
        discussion_prompt = (
            "Ask the trainee what they noticed, how the recorded sequence moved the scenario "
            "forward, and what they would want to review with an instructor."
        )

    return {
        "title": "Instructor review message",
        "summary": opening,
        "evidence": evidence,
        "discussion_prompt": discussion_prompt,
        "boundary": (
            "This is a deterministic POC discussion aid, not a grade, validated rubric, "
            "or operational judgment."
        ),
    }


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


def friendly_state(value: Any) -> str:
    if value is None:
        return "unknown"
    return str(value).replace("_", " ")


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


def review_headline(
    *,
    validation_counts: dict[str, int],
    end_reached: bool,
    final_phase: str | None,
) -> str:
    if validation_counts.get("error"):
        return "The run included an error that stopped at least one attempted action."
    if validation_counts.get("warning"):
        return "The run completed with POC warnings worth discussing in review."
    if end_reached:
        return "The run reached an end condition without recorded POC findings."
    return f"The run ended in phase '{final_phase or 'unknown'}' without reaching an end condition."


def key_observations(
    *,
    action_count: int,
    validation_counts: dict[str, int],
    end_reached: bool,
    environment: dict[str, Any],
) -> list[str]:
    observations = [
        f"The log captured {action_count} trainee action(s) in order.",
        f"The scenario end condition was {'reached' if end_reached else 'not reached'}.",
    ]
    if validation_counts.get("warning") or validation_counts.get("error"):
        observations.append(
            "The run included POC rule findings that are useful for review, not real-world scoring."
        )
    else:
        observations.append("No POC warnings or errors were recorded.")

    chair = environment.get("wooden_chair_poc")
    if chair:
        observations.append(
            "The wooden chair cue was "
            + ("cleared during the run." if chair.get("moved") else "still unresolved at the end.")
        )
    door = environment.get("entry_door_poc")
    if door:
        observations.append(
            "The entry door ended "
            + ("open." if door.get("open") else "closed or blocking the path.")
        )
    visibility = environment.get("smoke_visibility_cue_poc")
    if visibility:
        observations.append(
            "The smoke/visibility cue was "
            + ("checked before the final state." if visibility.get("observed") else "still unchecked at the end.")
        )
    room_cues = environment.get("room_cues")
    if room_cues:
        observations.append(
            "The room-level cues show "
            f"scan={yes_no(bool(room_cues.get('room_scanned')))}, "
            f"communication={yes_no(bool(room_cues.get('status_communicated')))}, "
            f"monitoring={yes_no(bool(room_cues.get('environment_monitored')))}, "
            f"occupant located={yes_no(bool(room_cues.get('occupant_located')))}."
        )
    return observations


def reviewer_takeaways(
    *,
    warnings: list[dict[str, Any]],
    errors: list[dict[str, Any]],
) -> list[str]:
    takeaways = [
        "This review explains deterministic POC behavior, not clinical or operational authority."
    ]
    if warnings:
        takeaways.append("Warnings show cues or sequence issues the scenario can discuss afterward.")
    if errors:
        takeaways.append("Errors show actions that did not conform to the toy scenario rules.")
    if not warnings and not errors:
        takeaways.append("The run followed the expected POC path without recorded findings.")
    return takeaways


def format_review_summary(
    summary: dict[str, Any],
    *,
    replay_result: dict[str, Any] | None = None,
    label: str | None = None,
    log_path: Path | str | None = None,
    physics_preview: str | None = None,
) -> str:
    """Render a human-friendly review for demos and command-line summaries."""

    warnings = summary.get("warnings") or []
    errors = summary.get("errors") or []
    validation_counts = summary.get("validation_counts") or {}
    action_count = summary.get("total_actions", len(summary.get("actions_taken") or []))
    lines = [
        "Post-scenario review",
        f"Session: {label or summary.get('session_id', 'unknown')}",
        f"Session ID: {summary.get('session_id', 'unknown')}",
        f"Scenario: {summary.get('scenario_id', 'unknown')}",
        f"What happened: {summary.get('review_headline', 'No headline generated.')}",
    ]
    if log_path is not None:
        lines.append(f"Log: {log_path}")
    lines.extend(
        [
            "",
            "Review snapshot:",
            f"  - Final phase: {summary.get('final_phase') or 'unknown'}",
            f"  - Scenario outcome: {summary.get('scenario_outcome') or 'unknown'}",
            f"  - End condition reached: {yes_no(bool(summary.get('end_condition_reached')))}",
            f"  - Actions reviewed: {action_count}",
            (
                "  - Validation counts: "
                f"ok={validation_counts.get('ok', 0)}, "
                f"warning={validation_counts.get('warning', 0)}, "
                f"error={validation_counts.get('error', 0)}"
            ),
        ]
    )
    if replay_result is not None:
        lines.extend(
            [
                f"  - Replay verified: {yes_no(bool(replay_result.get('verified')))}",
                f"  - Events replayed: {replay_result.get('events_replayed', 0)}",
            ]
        )
    if physics_preview is not None:
        lines.append(f"  - Physics preview shown: {physics_preview}")

    lines.extend(["", "Action timeline:"])
    action_timeline = summary.get("action_timeline") or []
    if not action_timeline and summary.get("actions_taken"):
        action_timeline = [
            {
                "sequence_number": index,
                "action_type": action,
                "validation_status": "not recorded in summary",
                "phase_after": None,
                "warning_codes": [],
                "error_codes": [],
            }
            for index, action in enumerate(summary["actions_taken"], start=1)
        ]
    for item in action_timeline:
        findings = [code for code in item.get("warning_codes", []) + item.get("error_codes", []) if code]
        finding_suffix = f" findings={', '.join(findings)}" if findings else ""
        lines.append(
            "  "
            f"{item.get('sequence_number')}. {item.get('action_type')} "
            f"-> {item.get('validation_status')} "
            f"-> phase={item.get('phase_after') or 'unknown'}"
            f"{finding_suffix}"
        )

    progress_stories = summary.get("progress_stories") or []
    if progress_stories:
        lines.extend(["", "Progress and retry story:"])
        lines.extend([f"  - {story}" for story in progress_stories])

    lines.extend(["", "Environment cues:", *environment_lines(summary.get("environment_review") or {})])
    lines.extend(["", f"Warning findings ({len(warnings)}):"])
    lines.extend(grouped_finding_lines(warnings) or ["  - none"])
    lines.extend(["", f"Error findings ({len(errors)}):"])
    lines.extend(grouped_finding_lines(errors) or ["  - none"])
    lines.extend(["", "Key observations:"])
    lines.extend([f"  - {item}" for item in summary.get("key_observations", [])])
    lines.extend(["", "Reviewer takeaways:"])
    lines.extend([f"  - {item}" for item in summary.get("reviewer_takeaways", [])])
    return "\n".join(lines)


def environment_lines(environment: dict[str, Any]) -> list[str]:
    room_cues = environment.get("room_cues")
    chair = environment.get("wooden_chair_poc")
    door = environment.get("entry_door_poc")
    visibility = environment.get("smoke_visibility_cue_poc")
    other_objects = environment.get("other_environment_objects") or {}
    lines: list[str] = []
    if room_cues:
        area_label = room_cues.get("area_label", "Room")
        lines.extend(
            [
                f"  - {area_label} cues:",
                f"    - {str(area_label).lower()} scanned: {yes_no(bool(room_cues.get('room_scanned')))}",
                f"    - door checked: {yes_no(bool(room_cues.get('door_checked')))}",
                f"    - status communicated: {yes_no(bool(room_cues.get('status_communicated')))}",
                f"    - environment monitored: {yes_no(bool(room_cues.get('environment_monitored')))}",
                f"    - exit path clear: {yes_no(bool(room_cues.get('exit_path_clear')))}",
                f"    - occupant visible: {yes_no(bool(room_cues.get('occupant_visible')))}",
                f"    - occupant located: {yes_no(bool(room_cues.get('occupant_located')))}",
                f"    - occupant guided: {yes_no(bool(room_cues.get('occupant_guided')))}",
                f"    - smoke density marker: {room_cues.get('smoke_density')}",
                f"    - visibility marker: {room_cues.get('visibility_level')}",
                f"    - air quality marker: {room_cues.get('air_quality_warning')}",
            ]
        )
    if chair:
        lines.extend(
            [
                "  - Wooden chair:",
                f"    - blocked path at end: {yes_no(bool(chair.get('blocked_path')))}",
                f"    - moved during scenario: {yes_no(bool(chair.get('moved')))}",
                f"    - physics flag: {yes_no(bool(chair.get('physics_enabled')))}",
                f"    - gravity note: {chair.get('gravity_note')}",
            ]
        )
    if door:
        lines.extend(
            [
                f"  - {door.get('label', 'Entry door')}:",
                f"    - open at end: {yes_no(bool(door.get('open')))}",
                f"    - blocks path at end: {yes_no(bool(door.get('blocked_path')))}",
                f"    - locked metadata: {yes_no(bool(door.get('locked')))}",
                f"    - door type metadata: {door.get('door_type')}",
            ]
        )
    if visibility:
        lines.extend(
            [
                f"  - {visibility.get('label', 'Smoke/visibility cue')}:",
                f"    - checked during scenario: {yes_no(bool(visibility.get('observed')))}",
                f"    - visibility level marker: {visibility.get('visibility_level')}",
                f"    - physics flag: {yes_no(bool(visibility.get('physics_enabled')))}",
                f"    - cue note: {visibility.get('cue_note')}",
            ]
        )
    for object_id, object_state in other_objects.items():
        lines.extend(
            [
                f"  - {object_state.get('label', object_id)}:",
                f"    - type: {object_state.get('object_type')}",
                f"    - location: {object_state.get('location')}",
                f"    - blocks path at end: {yes_no(bool(object_state.get('blocked_path')))}",
                f"    - moved marker: {object_state.get('moved')}",
                f"    - open state: {object_state.get('open_state')}",
                f"    - physics flag: {yes_no(bool(object_state.get('physics_enabled')))}",
            ]
        )
    return lines or ["  - no environment object state found"]


def finding_text(finding: dict[str, Any]) -> str:
    code = finding.get("code", "finding")
    message = finding.get("message", "No message")
    text = f"{code}: {message}"
    if finding.get("instructor_note"):
        text += f" Instructor note: {finding['instructor_note']}"
    return text


def grouped_finding_lines(findings: list[dict[str, Any]]) -> list[str]:
    grouped: dict[tuple[str, str, str], int] = {}
    order: list[tuple[str, str, str]] = []
    for finding in findings:
        key = (
            str(finding.get("code", "finding")),
            str(finding.get("message", "No message")),
            str(finding.get("instructor_note") or ""),
        )
        if key not in grouped:
            order.append(key)
            grouped[key] = 0
        grouped[key] += 1

    lines: list[str] = []
    for code, message, instructor_note in order:
        count = grouped[(code, message, instructor_note)]
        count_text = f" ({count}x)" if count > 1 else ""
        text = f"{code}{count_text}: {message}"
        if instructor_note:
            text += f" Instructor note: {instructor_note}"
        lines.append(f"  - {text}")
    return lines


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def first_object_by_type(objects: dict[str, Any], object_type: str) -> dict[str, Any]:
    for object_state in objects.values():
        if object_state.get("object_type") == object_type:
            return object_state
    return {}
