# Emergency Training Simulator POC: one-page handout

Prepared for Dr. Melissa Cameron.

## What this is

- Backend-first proof of concept for a future adaptive emergency-response training simulator.
- Current goal: prove the event/state/validation/log/review loop before adding heavy tools.
- Original vision includes AI, Unreal, sensing, validation, immersive environments, and deployment.
- Solo-developer checkpoint toward a much larger full-system vision.
- Scope control is how the larger idea stays buildable.

## What works today

- FastAPI WebSocket backend receives ordered trainee actions.
- Deterministic scenario engine updates state from YAML.
- POC validation returns `ok`, `warning`, or `error`.
- JSONL logs support replay and post-scenario review.
- Future Unreal display path can show backend-owned state as text.
- JSON-to-debug-text bridge exists for the first Unreal panel.

## Current demo

- Run `python scripts/run_local_demo.py`.
- Shows happy path and warning/error path.
- Replays session logs.
- Prints review summaries that explain what happened.
- Shows environmental cue status in plain English.

## Current scenario

- Tiny smoke-room software scenario.
- Blocked-exit hallway software scenario.
- `wooden_chair_poc` may block the path.
- `entry_door_poc` starts closed.
- Hallway obstacle and exit-door cues are tracked.
- Environment cues matter, but this is not real physics or field guidance.

## Boundaries

- No real AI calls yet.
- No clinical or protocol authority.
- No generated 3D assets.
- No Unreal scene or gameplay.
- No sensors, cloud deployment, or production security yet.

## Next direction

- Make Unreal read the generated debug text file.
- Then make Unreal parse display JSON.
- Then connect Unreal to the backend WebSocket.
- Keep the backend as the source of truth.
- Keep replay/review as the strongest proof point.
- Add simple scene/object visuals only after the display path is stable.
- Use Blender/manual review before trusting generated assets.

## Main takeaway

The system can track what happened, explain it afterward, and leave room for Unreal, AI, assets, sensing, and physics later.
