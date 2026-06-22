# System Layers

## Current target vertical slice

1. **API adapter** accepts client-neutral messages and rejects malformed envelopes.
2. **Orchestrator** enforces session order and coordinates one event transaction.
3. **Scenario engine** applies deterministic transitions from scenario data.
4. **Validation layer** reports rule conformance; it does not determine clinical truth.
5. **Models/contracts** represent events, state, and results consistently.
6. **Logging adapter** appends event, validation, and resulting state to local JSONL.
7. **Client adapter** returns a transport-neutral session message.

The first local vertical slice implements these layers with in-memory sessions and JSONL files.

## Future layers

Unreal presentation, remote transport, sensing adapters, AI-assisted authoring/adaptation, asset generation, and projection deployment remain behind adapters and are not part of the first vertical slice.
