# WebSocket error codes

The WebSocket endpoint returns simple error messages when a client sends something the backend cannot accept.

The shape is:

```json
{
  "message_type": "error",
  "code": "sequence_number_out_of_order",
  "message": "Expected sequence_number 1"
}
```

The `code` is for software. The `message` is for a human reading the demo output.

## Current codes

| Code | Meaning |
| --- | --- |
| `invalid_initial_message` | First message was not `start_session` or `trainee_action`. |
| `invalid_message` | Message shape failed Pydantic validation. |
| `unsupported_message` | Message type is not supported in the current WebSocket loop. |
| `invalid_session_id` | Session ID has unsafe characters or is too long. |
| `invalid_scenario_id` | Scenario ID has unsafe characters or is too long. |
| `session_already_exists` | A session with that ID already exists in this backend process. |
| `active_session_limit_reached` | Too many active sessions are already open. |
| `session_already_ended` | The client tried to continue after the scenario ended. |
| `session_action_limit_reached` | The session has already accepted the max number of actions. |
| `session_id_mismatch` | URL, envelope, and event session IDs do not match. |
| `scenario_id_mismatch` | Message scenario ID does not match the active scenario. |
| `sequence_number_mismatch` | Envelope and event sequence numbers do not match each other. |
| `sequence_number_out_of_order` | The client skipped or repeated the next expected sequence number. |
| `duplicate_event_id` | The event ID was already used in this session. |
| `correlation_event_id_mismatch` | Correlation ID does not match the trainee action event ID. |
| `unknown_session` | The backend does not know that session ID. |
| `session_error` | Fallback for an unexpected session-level problem. |

## Important note

These errors are local POC guardrails.

They do not replace authentication, authorization, TLS, production rate limiting, or deployment security.

