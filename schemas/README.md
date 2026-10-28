# Message Schemas

These checked-in JSON Schemas describe session messages and generic pipeline records.
Session models live in `backend/app/models/`; spatial plans/layouts are validated
by `arc/scripts/generate_scenario_batch.py`, and primitive physics contracts live
in `backend/app/physics/`. Asset request/automation contracts live in
`arc/scripts/asset_request.py` and `automation_contract.py`. Do not assume a
generic pipeline record is the exact live API payload.

They are the shared language between the fake trainee, backend, logs, scripts, and future Unreal client.

- `trainee_action_event`: one normalized trainee action
- `scenario_state`: the backend-owned state after an action
- `environment_object`: shared fields for simple scenario objects like chairs and doors
- `validation_result`: the POC rule result for that action
- `session_messages`: WebSocket messages for start, action, state update, end, and error

The examples are fixtures for development and tests. Schema version `0.1.0` can still change during the POC, so this is not a production compatibility promise.

Inbound IDs use a deliberately small character set: letters, numbers, underscores, and hyphens. Scenario IDs use lowercase letters, numbers, and underscores. Optional action payloads should stay small and JSON-shaped.

Always preserve `event_id` and `sequence_number` in logs. They make replay and review possible.

For repository-wide implementation and evidence, see [current status](../docs/current-status.md)
and the [documentation index](../docs/README.md).
