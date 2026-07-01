# Backend

This is the local FastAPI backend for the POC.

It does a small set of things on purpose:

- `GET /health` confirms the service is running.
- `/ws/sessions/{session_id}` starts a session and receives ordered trainee actions.
- The session manager applies scenario transitions, runs POC rule checks, sends state updates, and writes JSONL logs.
- Replay and summary scripts read the same logs later.

## Run it locally

From the repo root, after installing `.[dev]`:

```text
python -m uvicorn backend.app.main:app --reload
python scripts/run_fake_trainee.py
python -m pytest
```

The WebSocket defaults to `smoke_inhalation_room_v0`. A different checked-in scenario can be requested in the first `start_session` message.

This backend only proves the local action-to-state-to-log loop. It uses in-memory sessions and local files. There is no authentication, database, external AI, clinical decision support, distributed networking, sensing, deployment, or Unreal-specific gameplay logic.
