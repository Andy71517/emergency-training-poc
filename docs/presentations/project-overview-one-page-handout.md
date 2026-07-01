# Emergency Training Simulator POC: one-page handout

## What this is

This repo is a backend-first proof of concept for an AI-driven adaptive emergency-response training simulator.

It proves a small but important loop:

```text
trainee action -> backend -> scenario state -> validation -> client update -> log -> replay/review
```

## What it proves today

- A FastAPI backend can receive ordered trainee actions over WebSocket.
- A deterministic scenario engine can update state from a YAML scenario.
- POC validation rules can return `ok`, `warning`, or `error`.
- JSONL session logs can be written locally.
- Replay and review scripts can explain what happened after the run.
- A future Unreal client can follow a simple message contract.

## Current scenario

The current scenario is a tiny smoke-room POC.

It includes:

- a `wooden_chair_poc` object that may block the path
- an `entry_door_poc` object that starts closed
- actions like `move_obstacle` and `open_door`

This is a software scenario only. It is not medical, firefighter, EMT, or operational guidance.

## Current demo

Run:

```powershell
python scripts/run_local_demo.py
```

The demo runs:

- a happy path
- a warning/error path
- replay verification
- review summaries
- wooden-chair physics preview metadata

## Important boundary

This repo does not currently include:

- real AI or API calls
- clinical validation
- official emergency protocol authority
- generated 3D assets
- real physics
- a full Unreal scene
- sensors
- cloud deployment

## Next direction

The next work should keep the backend as the source of truth while making the future client contract clearer.

Near-term focus:

1. strengthen the display contract
2. keep replay and review central
3. add richer environment object metadata carefully
4. bring in Unreal only when the text/display contract is stable
5. use Blender for manual review before any generated asset is trusted

## Ideal end result

The long-term goal is an adaptive training simulator where environment cues matter, instructors can review sessions clearly, and future AI/3D/Unreal pieces support the training experience without hiding the system logic.

