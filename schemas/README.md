# Message Schemas

Draft 2020-12 JSON Schemas define the POC boundary between a fake trainee, backend layers, logs, and a future Unreal client.

- `trainee_action_event`: one normalized trainee action
- `scenario_state`: authoritative state after processing an event
- `validation_result`: conformance outcome for that event/transition
- `session_messages`: WebSocket handshake, action, state-update, terminal, and error messages

Examples are illustrative fixtures. Schema version `0.1.0` may change during the POC; production compatibility is not promised. Validate both incoming and outgoing messages and preserve `event_id` plus `sequence_number` in logs.
