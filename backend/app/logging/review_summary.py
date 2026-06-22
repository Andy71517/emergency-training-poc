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
        "actions_taken": actions,
        "warnings": warnings,
        "errors": errors,
        "end_condition_reached": end_reached,
    }
