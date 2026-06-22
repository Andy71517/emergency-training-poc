# POC Scope

## In scope for the first vertical slice

- One local process with a FastAPI health endpoint and WebSocket session endpoint
- Manual or scripted trainee actions
- One deterministic YAML scenario
- Ordered per-session transitions
- Schema-validated messages
- Rule-conformance results with warnings and errors
- Final state returned in a client-neutral JSON shape
- Append-only local JSONL session logging and replay
- Unit and API tests for happy, warning, unsafe, and terminal paths

## Sprint 0 deliverable

Repository organization, message schemas, a toy scenario, rule fixtures, ADRs, and implementation placeholders.

## Out of scope

Real AI calls, medical/operational authority, live sensors, multiplayer or distributed topology, Unreal gameplay, projection systems, 3D generation, production infrastructure, and field deployment.

## Success criterion

A later local demo can submit ordered stub events and show deterministic state, validation, client output, and replayable log entries without external services.
