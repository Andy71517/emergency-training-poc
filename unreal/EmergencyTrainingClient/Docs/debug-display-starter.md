> **Scaffold tutorial:** these instructions cover only the early session-display experiment. Current chair/room editor scripts and runtime evidence are described in [Unreal integration](../../README.md) and [current status](../../../docs/current-status.md).

# Debug Display Starter

This is the first tiny Unreal-facing implementation note.

The goal is not to build the simulator yet. The goal is only to prove that Unreal can display backend-owned state.

The easiest path is text first, JSON second.

That means:

```text
backend-shaped JSON
-> generated debug text
-> Unreal text panel
```

This avoids getting stuck on JSON parsing before the display idea is proven.

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

For the first pass, Unreal can load this simple text file:

- `Data/hallway_debug_panel.sample.txt`

That text file is generated from:

- `Data/display_state.sample.json`
- `Data/warning_display_state.sample.json`
- `Data/hallway_display_state.sample.json`

To refresh the text file:

```powershell
python scripts/write_unreal_debug_text.py
```

Later, Unreal can parse the JSON directly. After that, Unreal should receive this state through the backend WebSocket contract.

For the first actual Unreal setup, use `read-sample-json-debug-panel.md`.

## Boundary

Unreal displays state. The backend owns truth.
