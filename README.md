# Emergency Training Simulator POC

First vertical-slice proof of concept for a deterministic, AI-ready emergency-response training simulator. This repository is not an operational training, medical, or incident-response system.

## What the POC must prove

```text
manual/stubbed trainee action
  -> backend receives event
  -> scenario engine updates state
  -> validation rules check the transition
  -> final scenario state is produced
  -> client-facing state message is available
  -> event and outcome are logged for review
```

The implementation uses one small deterministic scenario, a FastAPI WebSocket, and local JSONL logs. Future AI components may help author or adapt scenarios, but they are not required to prove this loop.

## Setup and run

Python 3.11 or newer is required.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m uvicorn backend.app.main:app --reload
```

In another terminal, run the two scripted sessions:

```powershell
python scripts/run_fake_trainee.py
```

Run tests and inspect a generated session log:

```powershell
python -m pytest
python scripts/replay_session.py logs/sessions/demo-happy.jsonl
python scripts/summarize_log.py logs/sessions/demo-happy.jsonl
```

Clients first send `{"message_type":"start_session"}` to `/ws/sessions/{session_id}` and then send ordered `trainee_action` envelopes. Generated session logs remain ignored under `logs/sessions/`.

## Explicitly out of scope

- Real LLM or external API calls
- Clinical validity or authoritative EMT/firefighter protocol
- Production security, resilience, scaling, or deployment
- Hub-and-spoke networking, projection mapping, or multimodal sensing
- A full Unreal scene or generated 3D assets
- Autonomous evaluation of real responders

## Repository map

- `backend/`: FastAPI vertical slice and tests
- `schemas/`: versioned message contracts and examples
- `scenarios/`: deterministic scenario definitions
- `validation/`: POC rule-conformance definitions
- `docs/`: scope, architecture, ADRs, and demo plan
- `scripts/`: local run, replay, and review helpers
- `logs/`: ignored local JSONL session logs
- `unreal/`: placeholder for a future presentation client
- `assets/`: placeholders for a future reviewed asset pipeline

Start with [docs/overview.md](docs/overview.md) and [docs/sprint-0-plan.md](docs/sprint-0-plan.md).
