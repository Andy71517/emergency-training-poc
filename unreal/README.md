# Unreal integration

This folder contains Unreal 5.8 editor scripts and contracts. The working binary
project, generated maps/assets and engine outputs live outside Git; this checkout
does not include a complete `.uproject` or generated content.

## Current editor workflow

- `scripts/setup_unreal58_chair_demo.py` imports/binds the reviewed chair baseline.
- `scripts/prepare_unreal58_chair_presentation.py` prepares its presentation scene.
- `scripts/assemble_unreal58_rooms.py` creates per-room maps from validated room packages.
- `scripts/studio_bridge.py` polls the local checkout's command directory for fixed
  assemble/simulate/record work. Load once per editor session and keep Unreal open.
- `scripts/import_furniture_package.py` is bundled into the new generic furniture
  package; checks hashes, imports FBX/UCX, wires supported materials and checks size/hulls.

The user confirmed the existing chair demo, room assembly and ten-second Chaos
batches. First live recording and the new generic furniture import/collision cooking
remain unverified. New variants are not yet bound into chair-only room assembly.
See [current evidence](../docs/current-status.md).

## Guides

- [Studio/editor bridge](../docs/studio-pipeline-runbook.md)
- [Chair demo](../docs/unreal58-chair-demo-runbook.md)
- [Room batches](../docs/unreal58-room-batch-runbook.md)
- [Movement recording](../docs/visual-playback-runbook.md)
- [Furniture preparation and import](../docs/asset-automation-runbook.md)

Unreal imports the prepared FBX/textures/collision package. The `.blend` remains
the editable source. Hull naming/convexity checks are preparation evidence; actual
engine collision cooking and behavior must be checked in Unreal.

## Separate session-client contract

[contract/](contract/README.md) describes backend-owned session state and ordered
trainee actions. [EmergencyTrainingClient/](EmergencyTrainingClient/README.md) is
the earlier text-display scaffold, not the current external chair demo project.
The local editor job bridge does not implement that trainee WebSocket client.

The backend owns scenario transitions, validation, logs and review. Unreal supplies
rendering and engine observations; those are not operational guidance or trainee scores.
