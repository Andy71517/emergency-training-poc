# Unreal State Display Contract

This is the first Unreal-facing display contract.

The first Unreal client should be a text-only debug panel. No 2D UI polish, no scene, no assets, and no physics.

## What the panel should show

- session id
- scenario id
- current phase
- latest validation status
- one short status line
- warnings
- errors
- environment objects

For current objects, show:

- `wooden_chair_poc`: moved or still in path, blocking or not blocking
- `entry_door_poc`: open or closed, blocking or not blocking
- `smoke_visibility_cue_poc`: checked or unchecked

Each object row should also include an `alert_level`:

- `normal`: display it plainly
- `attention`: visually call it out in the debug panel

## What Unreal must not do

Unreal must not:

- decide scenario transitions
- change validation results
- infer hidden object state
- simulate physics
- load generated assets
- treat metadata as real collision, mass, force, or gravity

The backend owns the truth. Unreal displays what it receives.

## Local preview

Use this repo-side script before Unreal exists:

```powershell
python scripts/preview_unreal_display.py logs/sessions/demo-happy.jsonl
```

It prints the kind of text the future Unreal debug panel should show.

For JSON output matching the checked-in display contract:

```powershell
python scripts/preview_unreal_display.py logs/sessions/demo-happy.jsonl --json
```

## Checked-in examples

- `examples/display_state.example.json`: clean/happy display state
- `examples/warning_display_state.example.json`: warning display state
- `debug-display-state.schema.json`: schema for the simplified debug-display payload

This display payload is intentionally smaller than the full backend state message. It is the future Unreal debug panel's view model, not a new source of truth.
