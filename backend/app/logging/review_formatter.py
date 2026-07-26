"""Text and CLI output formatting for review summaries."""

from pathlib import Path
from typing import Any


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


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
