# Environment Object Contract

This contract keeps environment objects shaped the same way across the backend, logs, reviews, and future clients.

The backend still owns scenario state. These objects are not real 3D assets and do not run real physics.

## Required shared fields

Every environment object should include:

- `object_id`: the key used in `environment.objects`
- `object_type`: what kind of object it is, like `wooden_chair` or `door`
- `label`: short human-readable name
- `location`: simple scenario location label
- `blocks_path`: whether it currently blocks movement

## Optional shared metadata

Use these when helpful:

- `collision_enabled`: future-facing collision note
- `collision_shape`: simple future collision shape label
- `mass_kg_estimate`: rough future mass estimate
- `physics_enabled`: whether the scenario claims active physics; currently `false`
- `physics_note`: plain-language note about what is and is not simulated
- `force_preview`: future-facing notes about possible push/pull directions

These fields are metadata only right now. They do not create real gravity, collision, mass, or force behavior.

## Current object-specific fields

Wooden chair:

- `moved`: whether the chair has been moved aside

Entry door:

- `open_state`: `closed` or `open`
- `locked`: metadata only for now
- `door_type`: metadata only for now
- `hinge_side`: metadata only for now
- `swing_direction`: metadata only for now

## Current scenario objects

- `wooden_chair_poc`: starts near the entry path and blocks movement until `move_obstacle`.
- `entry_door_poc`: starts closed and blocks room entry until `open_door`.

## Blender review rule

When generated assets are introduced later, no asset should enter `assets/reviewed/` or Unreal until it passes a manual Blender review checklist.
