# Unreal State Display Contract

This is the first Unreal-facing display contract.

The first Unreal client should be a text-only debug panel. No 2D UI polish, no scene, no assets, and no physics.

## What the panel should show

- session id
- scenario id
- current phase
- latest validation status
- warnings
- errors
- environment objects

For current objects, show:

- `wooden_chair_poc`: moved or still in path, blocking or not blocking
- `entry_door_poc`: open or closed, blocking or not blocking

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
