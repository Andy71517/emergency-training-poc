# Funding-proof compute and application split

The approved direction separates the application, queued generation and immersive
runtime. Current deployment is local; CS Launch hosting is not implemented.
[Current status](../current-status.md) records evidence.

## Current implementation

| Location | Responsibility |
| --- | --- |
| Workstation | React/FastAPI studio, SQLite records, private settings, background Blender MCP/room workers and Unreal editor |
| ARC hosted service | Real structured room planning using the configured model/key |
| ARC Slurm allocation | Existing Hunyuan shape/paint runtimes; new pinned SDXL reference -> shape/paint asset job |
| User-controlled SSH agent | Noninteractive verified transport for backend-owned fixed GPU RPC |

The user confirmed hosted planning, generated chair and local Blender/Unreal room
workflows. New automated furniture dispatch is implemented but still needs SSH setup,
remote checkout update and its first live SDXL/couch run. A real native MCP/CoACD
fixture checks preparation independently of that remote acceptance.

## Intended CS Launch deployment

CS Launch is the proposed home for long-running UI/API, job metadata and future
authentication/database services. It should not be assumed to provide ARC's GPU
capacity or permission to submit jobs on behalf of users.

The current local SSH adapter is not an institutional service-access arrangement.
Before hosting, confirm the supported identity/delegation method, job ownership,
network/storage access, quotas, retention, secret handling and audit requirements.
Do not expose local workers or reuse a personal unlocked agent as a hosted service design.

## ARC generation and workstation runtime

Heavy model generation belongs in scheduled GPU jobs with reproducible model/source
revisions and retained stage evidence. Login nodes perform only light control work.
Interactive sessions/Open OnDemand remain useful for setup and recovery.

Blender currently runs locally and prepares copies with preserved source. Unreal
5.8 owns rendering, collision cooking and continuous physics observations. AI
geometry and collision proxies do not determine calibrated mass/material behavior
or clinical training meaning.

## End-to-end goal

```text
description -> reviewed plan and required asset inventory
  -> reuse reviewed designs / explicitly generate missing designs
  -> review geometry, materials, dimensions and collision preparation
  -> coordinated Blender environment and Unreal scene
  -> runtime interactions and backend-owned state/log/review
```

Today the room lane uses the accepted chair, while the new asset lane prepares
individual chair/couch designs. Mixed-asset resolution/footprints/bindings remain
the bridge between them. The legacy fixture authoring module is separate from
hosted spatial planning; a room plan is not a published training scenario.

## Research evidence to retain

Measure queue/inference/cleanup/import time, GPU/model/runtime identity, retries,
actual returned files, manual review effort, engine cooking and observed behavior.
Keep configured access, submission, generated output, prepared candidate and engine
acceptance distinct. Generation during active training is a later latency/validation
experiment, not a current real-time claim.

[Asset workflow](../asset-automation-runbook.md), [room studio](../studio-pipeline-runbook.md),
[roadmap](../roadmap.md), [security](../security/README.md).
