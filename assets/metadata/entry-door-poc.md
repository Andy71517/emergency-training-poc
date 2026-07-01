# Entry Door POC Object

**Status:** scenario metadata only. No mesh exists yet.

The smoke-room scenario now includes a simple entry door.

What matters now:

- `open_state`: `closed` or `open`
- `blocks_path`: whether the door blocks room entry

Metadata for later:

- `locked`
- `door_type`
- `hinge_side`
- `swing_direction`
- `collision_shape`
- `mass_kg_estimate`
- `force_preview`

The lock and door type do not control behavior yet. They are only notes for future work.

There is no real door physics, collision, force, lock simulation, Unreal scene, or generated door asset.
