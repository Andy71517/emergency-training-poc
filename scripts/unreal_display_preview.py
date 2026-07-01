"""Text-only display adapter for the future Unreal debug panel."""

from pathlib import Path
from typing import Any

from backend.app.logging.review_summary import generate_review_summary, load_jsonl


def display_state_from_log(path: Path) -> dict[str, Any]:
    summary = generate_review_summary(path)
    entries = load_jsonl(path)
    latest_validation = latest_validation_result(entries)
    final_state = summary.get("final_state") or {}
    return build_display_state(
        session_id=str(summary.get("session_id")),
        scenario_id=str(summary.get("scenario_id")),
        phase=str(final_state.get("phase", "unknown")),
        validation_status=str(latest_validation.get("status", "unknown")),
        warnings=summary.get("warnings") or [],
        errors=summary.get("errors") or [],
        environment_review=summary.get("environment_review") or {},
    )


def latest_validation_result(entries: list[dict[str, Any]]) -> dict[str, Any]:
    for entry in reversed(entries):
        validation = entry.get("validation_result")
        if validation:
            return validation
    return {}


def build_display_state(
    *,
    session_id: str,
    scenario_id: str,
    phase: str,
    validation_status: str,
    warnings: list[dict[str, Any]],
    errors: list[dict[str, Any]],
    environment_review: dict[str, Any],
) -> dict[str, Any]:
    return {
        "session_id": session_id,
        "scenario_id": scenario_id,
        "phase": phase,
        "validation_status": validation_status,
        "warnings": [finding_text(finding) for finding in warnings],
        "errors": [finding_text(finding) for finding in errors],
        "objects": object_display_rows(environment_review),
    }


def object_display_rows(environment_review: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    chair = environment_review.get("wooden_chair_poc")
    if chair:
        rows.append(
            {
                "object_id": "wooden_chair_poc",
                "label": chair.get("label", "Wooden chair"),
                "display": "moved aside" if chair.get("moved") else "still in path",
                "blocks_path": bool(chair.get("blocked_path")),
                "metadata": {
                    "location": chair.get("location"),
                    "physics_enabled": bool(chair.get("physics_enabled")),
                },
            }
        )
    door = environment_review.get("entry_door_poc")
    if door:
        open_state = str(door.get("open_state") or ("open" if door.get("open") else "closed"))
        rows.append(
            {
                "object_id": "entry_door_poc",
                "label": door.get("label", "Entry door"),
                "display": open_state,
                "blocks_path": bool(door.get("blocked_path")),
                "metadata": {
                    "locked": bool(door.get("locked")),
                    "door_type": door.get("door_type"),
                },
            }
        )
    return rows


def render_debug_panel(display_state: dict[str, Any]) -> str:
    lines = [
        "Unreal debug display preview",
        f"Session: {display_state['session_id']}",
        f"Scenario: {display_state['scenario_id']}",
        f"Phase: {display_state['phase']}",
        f"Validation: {display_state['validation_status']}",
        "",
        "Objects:",
    ]
    objects = display_state.get("objects") or []
    if not objects:
        lines.append("- no environment objects found")
    for object_row in objects:
        blocking = "blocking path" if object_row["blocks_path"] else "not blocking path"
        lines.append(f"- {object_row['label']}: {object_row['display']} ({blocking})")

    warnings = display_state.get("warnings") or []
    errors = display_state.get("errors") or []
    lines.extend(["", f"Warnings: {len(warnings)}"])
    lines.extend(f"- {warning}" for warning in warnings)
    lines.extend(["", f"Errors: {len(errors)}"])
    lines.extend(f"- {error}" for error in errors)
    lines.append("")
    lines.append("Text-only preview. Unreal must not own scenario logic.")
    return "\n".join(lines)


def finding_text(finding: dict[str, Any]) -> str:
    code = finding.get("code", "finding")
    message = finding.get("message", "No message")
    return f"{code}: {message}"
