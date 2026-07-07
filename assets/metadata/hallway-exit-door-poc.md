# Hallway Exit Door POC Object

**Status:** scenario metadata only. No mesh exists yet.

The blocked-exit hallway scenario includes a simple hallway exit door.

What matters now:

- `open_state`: `closed` or `open`
- `blocks_path`: whether the door blocks exit guidance
- `locked`: metadata only

Metadata for later:

- door type
- hinge side
- swing direction
- collision shape
- mass estimate
- force assumptions

There is no real door asset, lock behavior, collision, force, Unreal import, or physics simulation yet.

## Future asset notes

If this becomes a generated or sourced asset later:

- keep the shape simple
- make hinge/origin review explicit
- record whether the door is visual-only or a future motion/collision candidate
- do not imply real entry tactics, lock behavior, or door-force realism

The backend can track whether the door is open or closed.

The visual asset should only display that state later.

