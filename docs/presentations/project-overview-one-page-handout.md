# Emergency Training Simulator POC: one-page handout

## What this is

- Backend-first proof of concept for a future adaptive emergency-response training simulator.
- Current goal: prove the event/state/validation/log/review loop before adding heavy tools.
- First audience: Dr. Cameron, as a project progress and direction update.

## What works today

- FastAPI WebSocket backend receives ordered trainee actions.
- Deterministic scenario engine updates state from YAML.
- POC validation returns `ok`, `warning`, or `error`.
- JSONL logs support replay and post-scenario review.
- Future Unreal client contract can display backend-owned state.

## Current demo

- Run `python scripts/run_local_demo.py`.
- Shows happy path and warning/error path.
- Replays session logs.
- Prints review summaries that explain what happened.
- Includes wooden-chair physics preview metadata only.

## Current scenario

- Tiny smoke-room software scenario.
- `wooden_chair_poc` may block the path.
- `entry_door_poc` starts closed.
- Environment cues matter, but this is not real physics or field guidance.

## Boundaries

- No real AI calls yet.
- No clinical or protocol authority.
- No generated 3D assets.
- No Unreal scene or gameplay.
- No sensors, cloud deployment, or production security yet.

## Next direction

- Keep the backend as the source of truth.
- Keep replay/review as the strongest proof point.
- Improve the future client display contract.
- Add richer object metadata carefully.
- Use Blender/manual review before trusting generated assets.

## Main takeaway

The system can track what happened, explain it afterward, and leave room for Unreal, AI, assets, sensing, and physics later.
