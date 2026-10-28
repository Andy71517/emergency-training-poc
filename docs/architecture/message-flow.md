# Message Flow

This is the deterministic session path. Hosted room planning and the ARC/MCP asset lane have separate persisted job/artifact flows; see [system layers](system-layers.md) and [current status](../current-status.md).

```text
fake/manual trainee
  -> TraineeActionEvent
  -> API schema check
  -> POC input guardrails
  -> per-session sequence check
  -> deterministic transition
  -> ValidationResult
  -> ScenarioState
  -> append SessionMessage record to JSONL
  -> return a client-ready SessionMessage
```

The session manager treats one action as one ordered step. It records the incoming action, validation result, and resulting state together.

Rejected actions are logged too. That way review can show what was attempted, even when the scenario state did not move forward.

Important IDs:

- `session_id` groups one run.
- `event_id` identifies one trainee action.
- `sequence_number` defines the order.
- `timestamp` helps review, but does not decide the scenario state.
