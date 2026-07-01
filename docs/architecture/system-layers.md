# System Layers

This project is split into small layers so each part has one clear job.

## Current backend slice

1. **API layer** receives WebSocket messages and rejects messages that do not match the contract.
2. **Session manager** keeps actions in order for one session.
3. **Scenario engine** applies the next state change from scenario data.
4. **Validation layer** checks POC rules and returns `ok`, `warning`, or `error`.
5. **Models and contracts** keep events, state, and messages shaped consistently.
6. **Logger** writes each step to local JSONL for replay and review.
7. **Client message layer** sends state back in a format any client can read.

The first slice uses in-memory sessions and local files. That is enough for the POC.

## Future areas

Unreal rendering, remote networking, sensing, AI-assisted authoring, asset generation, and projection deployment are future work. They should connect through clear contracts instead of owning scenario logic.
