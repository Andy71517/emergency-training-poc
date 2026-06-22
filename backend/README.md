# Backend Vertical Slice

This directory contains the local deterministic FastAPI proof of concept.

Current responsibilities:

- `GET /health` reports local service status.
- `/ws/sessions/{session_id}` accepts a `start_session` handshake and ordered trainee actions.
- The session manager coordinates YAML transitions, POC rule conformance, state updates, terminal messages, and JSONL records.
- Replay and summary helpers consume the same logged contracts.

## Run locally

From the repository root after installing `.[dev]`:

```text
python -m uvicorn backend.app.main:app --reload
python scripts/run_fake_trainee.py
python -m pytest
```

The WebSocket defaults to `smoke_inhalation_room_v0`; an alternate checked-in scenario may be named in the initial `start_session` message.

The backend currently proves only the local action-to-state-to-log loop. It has in-memory sessions and local files, with no authentication, database, external AI, clinical decision support, distributed networking, sensing, deployment, or Unreal-specific logic.
