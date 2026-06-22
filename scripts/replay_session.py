"""Replay processed action records and verify their deterministic state snapshots."""

import argparse
from pathlib import Path

from backend.app.logging.review_summary import load_jsonl
from backend.app.models.messages import TraineeActionMessage
from backend.app.scenario_engine.engine import ScenarioEngine
from backend.app.scenario_engine.loader import load_scenario
from backend.app.validation.rules import load_rules
from backend.app.validation.validator import ScenarioValidator


def replay(path: Path) -> dict[str, object]:
    entries = load_jsonl(path)
    if not entries:
        raise ValueError("Session log is empty")
    scenario = load_scenario(entries[0]["scenario_id"])
    engine = ScenarioEngine(scenario)
    validator = ScenarioValidator(scenario, load_rules(scenario.scenario_id))
    state = engine.initial_state()
    processed = 0

    for entry in entries:
        if entry.get("event_type") != "action_processed":
            continue
        message = TraineeActionMessage.model_validate(entry["inbound_message"])
        if message.sequence_number != processed + 1:
            raise ValueError(f"Non-contiguous sequence at {message.sequence_number}")
        candidate = engine.preview_action(state, message.trainee_action.action_type)
        evaluation = validator.evaluate(
            message.trainee_action,
            current_state=state,
            candidate_state=candidate.state,
            transition_note=candidate.note,
        )
        if not evaluation.blocks_transition:
            state = candidate.state
        processed += 1
        if state != entry.get("state_snapshot"):
            raise ValueError(f"Replay mismatch at sequence {processed}")

    return {"events_replayed": processed, "final_state": state, "verified": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    result = replay(parser.parse_args().log)
    print(f"Verified {result['events_replayed']} events; final state: {result['final_state']}")
