# Message Flow

## Current local POC flow

```text
fake/manual trainee
  -> TraineeActionEvent
  -> API schema check
  -> per-session sequence check
  -> deterministic transition
  -> ValidationResult
  -> ScenarioState
  -> append SessionMessage record to JSONL
  -> return client-neutral SessionMessage
```

The orchestrator should commit the event, validation outcome, and resulting state as one logical ordered record. Rejected or non-transitioning events are also logged with their unchanged state so review does not lose attempted actions.

`session_id` groups a run, `event_id` provides event identity, and `sequence_number` establishes order. Timestamps support review but must not drive deterministic transitions.
