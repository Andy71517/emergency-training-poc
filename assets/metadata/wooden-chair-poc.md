# Wooden chair: toy object and generated baseline

The name refers to two distinct records:

- `wooden_chair_poc` in deterministic scenarios is a software environment cue. Its
  `physics_enabled` preview metadata does not run a physics engine.
- The actual reviewed chair used by spatial demos was generated with Hunyuan on
  ARC: shape job **8052814**, paint job **8053348**. Blender 5.1.2 repair, floor pivot
  and **19** convex pieces were accepted. The user confirmed Unreal 5.8 drop/settle
  and room/Chaos behavior. This binary lives at the workstation's `CHAIR_BLEND` path.

Do not use the toy metadata as evidence of generated geometry or engine motion.
The real chair's generation and limited demo observations are not calibrated
physical measurements or training validation.

Existing room assembly reuses the reviewed chair binding. New designs need their
own quality/collision review and downstream bindings; do not copy this chair's
19-piece recipe blindly. [Current evidence](../../docs/current-status.md),
[asset pipeline](../../docs/architecture/generated-asset-pipeline.md).
