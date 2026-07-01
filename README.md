# Emergency Training Simulator POC

This repo is a small proof of concept for an emergency-response training simulator idea.

The goal is not to build the final product yet. The goal is to prove one simple loop: a trainee does something, the backend receives it, the scenario state changes in a predictable way, the result gets checked, the client receives the new state, and the session is logged for review.

This is not a real training system, medical tool, firefighting authority, or incident-response system.

## The loop we are proving

```text
manual/stubbed trainee action
  -> backend receives event
  -> scenario engine updates state
  -> validation rules check the transition
  -> final scenario state is produced
  -> client-facing state message is available
  -> event and outcome are logged for review
```

Right now this uses one tiny scenario, a FastAPI WebSocket, deterministic Python code, and local JSONL logs. Future AI pieces might help create or adapt scenarios later, but this first version does not need real AI calls.

## Setup and run

Use Python 3.11 or newer.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m uvicorn backend.app.main:app --reload
```

For the cleanest end-to-end walkthrough, run the one-command local demo:

```powershell
python scripts/run_local_demo.py
```

It starts the backend if needed, runs demo sessions, replays the logs, prints review summaries, and shows the wooden-chair environment preview with physics disabled and enabled.

The toy smoke-room scenario now includes a wooden chair and an entry door near the path into the room. The happy path moves the chair with `move_obstacle`, opens the door with `open_door`, and then enters. If the trainee ignores either cue, the backend returns a warning and does not advance the room-entry step.

In another terminal, run the fake trainee demo:

```powershell
python scripts/run_fake_trainee.py
```

To test the future Unreal client contract, without building an Unreal scene:

```powershell
python scripts/run_unreal_contract_harness.py
```

Run tests and inspect a generated session log:

```powershell
python -m pytest
python scripts/replay_session.py logs/sessions/demo-happy.jsonl
python scripts/summarize_log.py logs/sessions/demo-happy.jsonl
```

Clients start by sending `{"message_type":"start_session"}` to `/ws/sessions/{session_id}`. After that, they send ordered `trainee_action` messages. Generated session logs live under `logs/sessions/` and are ignored by Git.

## What this repo is not doing

- Real LLM or external API calls
- Clinical validation or EMT/firefighter protocol authority
- Production security, scaling, deployment, or cloud infrastructure
- Hub-and-spoke networking
- Projection mapping
- Multimodal sensing
- A full Unreal scene
- Generated 3D assets
- Real physics simulation
- Autonomous evaluation of real responders

## Security baseline

The backend now has a small POC security baseline. It rejects strange IDs, unexpected message fields, path-like scenario names, oversized/nested payloads, too many active sessions, and too many actions in one session.

This does not make the app production-secure. There is still no authentication, authorization, TLS, rate limiting, cloud deployment, or real data handling policy.

Start with [docs/security/README.md](docs/security/README.md) for the current trust boundary.

## Repository map

- `backend/`: FastAPI backend, deterministic engine, validation, logging, and tests
- `schemas/`: JSON message contracts and examples
- `scenarios/`: small scenario definitions
- `validation/`: rule files for the toy scenario
- `docs/`: scope, architecture notes, ADRs, and demo flow
- `docs/security/`: POC threat model, client trust boundary, and security roadmap
- `scripts/`: local demo, replay, summary, and contract helpers
- `logs/`: local JSONL session logs, ignored by Git
- `unreal/`: future Unreal client contract and placeholder folder
- `assets/`: placeholder folders for a future reviewed asset pipeline

Start with [docs/overview.md](docs/overview.md) and [docs/sprint-0-plan.md](docs/sprint-0-plan.md).
