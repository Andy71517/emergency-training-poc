# Unreal Client Contract

This folder describes how a future Unreal client should talk to the backend.

There is no Unreal scene here. This is just the contract.

The future client has a small job:

- Open one WebSocket session to the backend.
- Send contract-shaped `start_session` and `trainee_action` messages.
- Receive state, validation results, and scenario end messages from the backend.
- Display that state later, when an Unreal scene exists.

The client must not own scenario transitions, validation rules, trainee scoring, logs, clinical interpretation, or operational protocol authority.

## Files

- `client-contract.md`: how the WebSocket session works.
- `client-state-machine.md`: the smallest useful client-side state machine.
- `state-display-contract.md`: what the first text-only Unreal debug panel should show.
- `debug-display-state.schema.json`: JSON schema for the simplified text debug-display state.
- `examples/`: example JSON messages for review and tests, including smoke-room and blocked-exit hallway display-state samples.
