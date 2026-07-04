# Debug Display Starter

This is the first tiny Unreal-facing implementation note.

The goal is not to build the simulator yet. The goal is only to prove that Unreal can display backend-owned state.

## What to build first in Unreal

Build a plain text debug panel that can show:

- session ID
- scenario ID
- phase
- validation status
- status line
- warnings
- errors
- environment object rows

Each object row should show:

- label
- display text
- whether it blocks the path
- alert level

Example row:

```text
[attention] Smoke/visibility cue: unchecked (not blocking path)
```

## What not to build yet

Do not build:

- a full scene
- 3D assets
- gameplay interactions
- physics
- sensing
- projection mapping
- local scenario rules
- local validation or scoring

## Data source

For the first pass, Unreal can load one of the local sample files:

- `Data/display_state.sample.json`
- `Data/warning_display_state.sample.json`

Later, Unreal should receive this state through the backend WebSocket contract.

## Boundary

Unreal displays state. The backend owns truth.
