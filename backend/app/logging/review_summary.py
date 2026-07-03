"""Generate a readable review from one ordered POC session log."""

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
                "validation_status": status,
                "warning_codes": [item.get("code") for item in validation.get("warnings", [])],
                "error_codes": [item.get("code") for item in validation.get("errors", [])],
                "phase_after": (state_snapshot or {}).get("phase"),
                "outcome_after": (state_snapshot or {}).get("scenario_outcome"),
                "state_changed": previous_action_state is None or previous_action_state != state_snapshot,
            }
            action_timeline.append(timeline_item)
            if isinstance(state_snapshot, dict):
                previous_action_state = state_snapshot
        warnings.extend(validation.get("warnings", []))
        errors.extend(validation.get("errors", []))
        if state_snapshot is not None:
            final_state = state_snapshot
        end_reached = end_reached or entry.get("event_type") == "scenario_ended"

    review = environment_review(final_state)
    headline = review_headline(
        validation_counts=validation_counts,
        end_reached=end_reached,
        final_phase=final_state.get("phase"),
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


def environment_review(state: dict[str, Any]) -> dict[str, Any]:
    objects = state.get("environment", {}).get("objects", {})
    chair = objects.get("wooden_chair_poc", {})
    door = objects.get("entry_door_poc", {})
    visibility = objects.get("smoke_visibility_cue_poc", {})
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

    lines.extend(["", "Environment cues:", *environment_lines(summary.get("environment_review") or {})])
    lines.extend(["", f"Warnings ({len(warnings)}):"])
    lines.extend([f"  - {finding_text(finding)}" for finding in warnings] or ["  - none"])
    lines.extend(["", f"Errors ({len(errors)}):"])
    lines.extend([f"  - {finding_text(finding)}" for finding in errors] or ["  - none"])
    lines.extend(["", "Key observations:"])
    lines.extend([f"  - {item}" for item in summary.get("key_observations", [])])
    lines.extend(["", "Reviewer takeaways:"])
    lines.extend([f"  - {item}" for item in summary.get("reviewer_takeaways", [])])
    return "\n".join(lines)


def environment_lines(environment: dict[str, Any]) -> list[str]:
    chair = environment.get("wooden_chair_poc")
    door = environment.get("entry_door_poc")
    visibility = environment.get("smoke_visibility_cue_poc")
    lines: list[str] = []
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
                "  - Entry door:",
                f"    - open at end: {yes_no(bool(door.get('open')))}",
                f"    - blocks path at end: {yes_no(bool(door.get('blocked_path')))}",
                f"    - locked metadata: {yes_no(bool(door.get('locked')))}",
                f"    - door type metadata: {door.get('door_type')}",
            ]
        )
    if visibility:
        lines.extend(
            [
                "  - Smoke/visibility cue:",
                f"    - checked during scenario: {yes_no(bool(visibility.get('observed')))}",
                f"    - visibility level marker: {visibility.get('visibility_level')}",
                f"    - physics flag: {yes_no(bool(visibility.get('physics_enabled')))}",
                f"    - cue note: {visibility.get('cue_note')}",
            ]
        )
    return lines or ["  - no environment object state found"]


def finding_text(finding: dict[str, Any]) -> str:
    code = finding.get("code", "finding")
    message = finding.get("message", "No message")
    return f"{code}: {message}"


def yes_no(value: bool) -> str:
    return "yes" if value else "no"
