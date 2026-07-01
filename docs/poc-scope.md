# POC Scope

## In scope

- One local FastAPI backend
- A health endpoint and a WebSocket session endpoint
- Manual or scripted trainee actions
- One small YAML scenario
- Ordered actions inside a session
- Pydantic and JSON Schema message contracts
- Rule checks that return `ok`, `warning`, or `error`
- JSON state updates that any client can read
- Local JSONL logs that can be replayed and summarized
- Tests for happy paths, warnings, errors, determinism, logging, and WebSockets
- A thin future-Unreal client contract, with no Unreal scene

## Out of scope

This repo is intentionally not doing:

- Real AI or LLM calls
- Medical or operational authority
- Live sensors
- Multiplayer or distributed networking
- Unreal gameplay or rendering
- Projection systems
- 3D asset generation
- Production infrastructure
- Field deployment

## Success criterion

A local demo should be able to send ordered stub actions and show the full path: backend input, deterministic state update, validation result, client message, log entry, replay, and summary.
