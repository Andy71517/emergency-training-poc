# Message Schemas

These JSON Schemas describe the messages that move through the POC.

They are the shared language between the fake trainee, backend, logs, scripts, and future Unreal client.

- `trainee_action_event`: one normalized trainee action
- `scenario_state`: the backend-owned state after an action
- `environment_object`: shared fields for simple scenario objects like chairs and doors
- `validation_result`: the POC rule result for that action
- `session_messages`: WebSocket messages for start, action, state update, end, and error

The examples are fixtures for development and tests. Schema version `0.1.0` can still change during the POC, so this is not a production compatibility promise.

Always preserve `event_id` and `sequence_number` in logs. They make replay and review possible.
