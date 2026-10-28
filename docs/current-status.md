# Current implementation and evidence

Documentation reviewed **October 28, 2026**, against `main` after implementation
commits `7085e76` and `3b50f6f`. This is a documentation checkpoint; no new remote
GPU job or Unreal run is implied. [Documentation index](README.md).

## Evidence levels

| Capability | Implemented behavior | Verified evidence / outstanding check |
| --- | --- | --- |
| Hosted room planning | ARC `gpt-oss-120b`, bounded plan validation, seeded layouts and persistent batch records | User confirmed live frontend planning. The model key is independent of GPU SSH access. |
| Chair asset baseline | Hunyuan3D-2.1 shape/paint; reviewed Blender chair with 19 convex pieces | Shape job 8052814 and paint job 8053348 completed. User accepted the prepared chair. |
| Room assembly | Background Blender file/render/report; Unreal editor bridge and per-room maps | User confirmed local Blender room assembly, Unreal 5.8 assembly and ten-second Chaos batches. |
| Recording | Fixed editor capture, saved frames, FFmpeg MP4 encoding/retry and download | Protocol/fake-editor tests and real local encoding passed. First live engine screenshot/MP4 verification remains pending. |
| Description-based asset job | Pinned SDXL reference, Hunyuan shape/paint, SSH submit/status/download, dispatch recovery and bound package import | Code and offline tests pass. First actual SDXL inference in the ARC runtime and first automated couch job remain unrun. |
| Blender MCP preparation | Scoped stdio tools, conservative cleanup, CPU CoACD, named UCX hulls, packed `.blend`, preview, FBX and Unreal package | Real Blender 5.1.2 + MCP + CoACD ran on an explicitly synthetic fixture: 28 closed hulls, 29-mesh FBX roundtrip, packed file reopened. Not a generated couch result. |
| Generic Unreal furniture importer | Hash/material preflight, FBX/UCX import, PBR wiring, size/hull checks | Compile/preflight checks only. Actual Unreal API behavior and collision cooking remain unverified. |
| Session baseline | Two deterministic YAML scenarios, ordered WebSocket actions, validation, JSONL replay/review | Offline regression tests. Independent of room layouts and engine observations. |
| Legacy scenario authoring | In-memory fixture suggestion, full-field edits and revision-bound approval | Still deliberately mocked. It is separate from the real hosted room planner. |

## Current operating path

1. Run the local app from `main`; use port 8772 for the one-port guide.
2. Use the existing reviewed chair for scenario room batches.
3. For new furniture, use **Asset library -> Describe it. Build it.** after the
   connection check succeeds. Manual reference/request/result ZIPs remain optional.
4. Review actual geometry, staged dimensions, materials and collision fit. Import
   the prepared FBX package into Unreal; `.blend` is the editable source.
5. New variants remain unavailable to room placement until planner/footprint,
   Blender and Unreal bindings are extended together.

The October 26 local installation retained the reference-only couch request
`64e106d0434281a2a919e2d7e7706dd8a17d18f48b5f9be767a185fa7a55ce52`.
Its `ready_for_arc` state means a request exists, not that generation happened.
No automated dispatch existed at that check. Current local runtime state may differ;
inspect the app rather than inferring connectivity from a configured badge.

## Remaining prerequisites and next checks

- Establish verified noninteractive SSH access using user-controlled host trust and
  an unlocked local agent, then update the ARC checkout. The last check failed
  because no trusted ED25519 host key was known. No credential/trust setup changed.
- Run the first automated couch job, retain the actual Slurm ID and returned lineage,
  and review the real output. Connection loss must resume the same dispatch.
- Exercise the generic importer in Unreal 5.8 and inspect materials, collision cooking,
  gaps, scale and contact behavior.
- Verify the first live recorded movement clip.
- Integrate reviewed mixed-furniture footprints/IDs across planning and both assemblers.

## Checks and source pointers

The last implementation batch passed **138 backend/ARC tests**, Ruff, compilation,
Bash syntax, JSON checks, frontend lint/build and GitHub CI. Those checks do not
prove live GPU inference or Unreal execution. Native fixture evidence is described
separately above and in the [October 26 handoff](arc-handoff-2026-10-26.md).

- [Asset automation and one-time setup](asset-automation-runbook.md)
- [Room studio](studio-pipeline-runbook.md)
- [Current gaps](full-system-gap-map.md) and [roadmap](roadmap.md)
- [Historical October 19 evidence](arc-handoff-2026-10-19.md)

PRs #1-#7 were merged before this batch. Use `main`; dated branch/PR instructions
in earlier handoffs are history. CS Launch hosting, multi-user security, sensing,
clinical validation and arbitrary complete-scene automation remain future work.
