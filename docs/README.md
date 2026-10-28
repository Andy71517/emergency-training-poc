# Documentation index

Reviewed October 28, 2026. Start with [current status and evidence](current-status.md)
or the [repository README](../README.md). Current setup uses `main`; old handoffs
and plans record decisions at their dates and may contain superseded commands.

## Run the system

| Task | Guide |
| --- | --- |
| Install and run the local studio | [Workspace setup](arc-workspace-runbook.md) |
| Generate layouts and assemble chair rooms | [Studio pipeline](studio-pipeline-runbook.md) |
| Describe furniture, run ARC and prepare with Blender MCP | [Asset automation](asset-automation-runbook.md) |
| Bring an existing PNG / manually transfer request/result ZIPs | [Furniture variants](furniture-variants-runbook.md) |
| Run the original session/replay/review proof | [Demo script](demo-script.md) |
| Record and review Unreal movement clips | [Visual playback](visual-playback-runbook.md) |
| Reproduce the existing chair pipeline manually | [Shape](arc-hunyuan-runbook.md), [paint](arc-hunyuan-texture-runbook.md), [repair](blender-chair-repair-runbook.md), [collision](blender-chair-collision-runbook.md), [export](blender-chair-unreal-export-runbook.md) |
| Use the existing Unreal chair/room tools | [Chair demo](unreal58-chair-demo-runbook.md), [presentation](unreal58-chair-presentation-runbook.md), [room batches](unreal58-room-batch-runbook.md) |
| Inspect batch reuse and recoverable Trash | [History and assets](batch-history-and-assets.md) |
| Run repository checks | [Development / CI](development/ci.md) |

## Understand the project

- [Overview](overview.md), [scope](poc-scope.md), [roadmap](roadmap.md), [gap map](full-system-gap-map.md)
- [Full vision](full-project-vision.md) and [original reference](reference/README.md)
- [System layers](architecture/system-layers.md), [message flow](architecture/message-flow.md)
- [Asset pipeline](architecture/generated-asset-pipeline.md), [object contract](architecture/environment-object-contract.md)
- [Compute split](architecture/funding-proof-platform.md), [Unreal integration](architecture/future-unreal-client.md), [physics proof](architecture/visual-physics-proof.md)
- [Security](security/README.md), [UX](ux/README.md), [architecture decisions](adr/0007-split-application-generation-and-runtime-compute.md)
- [Reports and PDF packet](reports/README.md), [presentation package](presentations/README.md)

## Checkpoints and original plans

The latest implementation evidence is the [October 26 handoff](arc-handoff-2026-10-26.md).
Earlier checkpoints: [October 19](arc-handoff-2026-10-19.md),
[October 18](arc-handoff-2026-10-18.md), [October 4](arc-handoff-2026-10-04.md),
[September 28](arc-handoff-2026-09-28.md).

Original plans remain useful context: [asset automation plan](asset-automation-plan.md),
[prompt-to-scene plan](prompt-to-scene-batch-plan.md),
[first ARC/Blender/Unreal plan](arc-blender-unreal-pipeline-plan.md),
[Sprint 0](sprint-0-plan.md). Use the current runbooks for execution.

Future architecture notes for [sensing](architecture/future-sensing-adapters.md),
[hub-and-spoke](architecture/future-hub-and-spoke.md) and
[projection](architecture/future-projection-deployment.md) describe goals, not deployed features.
