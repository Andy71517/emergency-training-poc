# FIELDWORK project progress report

Prepared for Dr. Melissa Cameron. Documentation checkpoint: October 28, 2026.
Based on the implementation through `3b50f6f`; no new live GPU or engine result is
implied by this report date.

## Executive summary

FIELDWORK has progressed from a deterministic backend foundation to a local
scenario studio with hosted ARC room planning, persistent layouts/history, Blender
room assembly and an Unreal 5.8 editor bridge. The user confirmed the generated
chair, room assembly and bounded Chaos demonstrations.

The latest implementation adds description-based furniture generation, fixed
SSH/Slurm submission/retrieval and Blender MCP preparation. It is designed to take
a description through an internally generated reference, Hunyuan shape/paint,
cleanup/collision preparation and editable Blender/Unreal packages. The first live
automated couch remains blocked on one-time SSH setup and a remote checkout update.
Native preparation was verified on a synthetic fixture; this is not couch evidence.

The complete-environment goal remains larger: resolve reviewed assets, generate
missing designs explicitly, use actual footprints and assemble the same mixed
scene in Blender and Unreal. Current room contracts still use the reviewed chair.

## Full-system direction

The long-term vision is an adaptive emergency-response training platform with
immersive environments, trainee sensing, mannequin/projection integration,
structured validation and explainable review. FIELDWORK is not that finished
platform. Live adaptation, domain-validated training content, sensing and production
deployment remain research/integration work.

## Working foundation

Two deterministic toy scenarios exercise the same ordered session loop:

```text
attempted action -> backend validation/state -> client update
  -> ordered JSONL -> replay -> instructor discussion summary
```

The smoke-room and blocked-exit hallway fixtures test cues, sequencing, accepted
actions and warning/error paths. Review explains actions, state changes, retries
and findings. It is not a trainee grade, protocol judgment or clinical evaluation.
The legacy draft/edit/approve module remains a separate in-memory fixture workflow.

## Spatial room studio

The real hosted ARC planner proposes structured room data. The backend validates
bounded plans, generates seeded layouts and saves SQLite job/artifact records.
The UI provides previews, downloads, exact-input reuse, replay and recoverable
Trash. Model failure does not silently produce fixture results.

The reviewed wooden chair is the current room binding. Local Blender builds room
files/renders/reports, while the open Unreal editor bridge assembles per-room maps
and reports ten-second Chaos observations. The user confirmed these workflows.
Geometric aisle overlap is not navigation or evacuation validation; endpoint
movement does not prove collision contacts or calibrated physical behavior.

## Generated furniture and Blender MCP

The asset library supports named chair/couch variants. A new description-based
dispatch generates a pinned SDXL reference on ARC, then uses existing Hunyuan
shape/paint runtimes. Manual reference/request/result ZIPs remain an alternative.

The backend owns verified noninteractive SSH commands and saved dispatch identity.
Remote journals and scheduler comments recover uncertain submissions without
blindly submitting another GPU job. Returned packages bind prompt, reference,
model revisions, scheduler ID and file hashes before import.

A real stdio MCP client calls scoped inspection/preparation tools. Fixed Blender
scripts preserve the source, clean a copy conservatively, uniformly match height,
ground/center and extract material data. Isolated CPU CoACD creates checked convex
proxies. Outputs include a packed editable `.blend`, preview, preparation report,
FBX, textures, UCX hulls and a generic Unreal import helper.

Automatic cleanup does not reconstruct arbitrary missing/fused geometry. Target
width/depth are not enforced by stretching the model; actual dimensions and
mismatches are reported. Appearance, gaps, collision fit and material limitations
require whole-result review. A prepared package does not make a new design room-ready.

## Evidence ledger

- Real ARC chair shape job 8052814 and paint job 8053348 completed. Blender 5.1.2
  repair and 19 convex pieces were accepted; the user confirmed the Unreal chair demo.
- The user confirmed hosted frontend room planning, local Blender assembly and
  Unreal 5.8 room/Chaos batches.
- Real Blender 5.1.2, MCP and CoACD prepared an explicitly synthetic furniture
  fixture: 28 closed hulls, 29-mesh FBX roundtrip and a reopened packed Blender file.
  Its size mismatch was correctly reported. This was not a generated couch.
- The implementation checkpoint passed 138 backend/ARC tests, frontend lint/build,
  Ruff, compilation, Bash syntax, JSON and GitHub CI.
- Recording protocol tests and local FFmpeg encoding passed. First live Unreal
  frame/MP4 acceptance remains pending.
- First automatic SDXL/couch inference and the new generic Unreal importer/material
  APIs/collision cooking remain unrun. Offline checks are not substitutes.

## Compute, storage and security

The current application is a local single-user FastAPI/React process. ARC supplies
hosted planning and scheduled GPU generation. Blender and Unreal run on the
workstation. CS Launch hosting is a future deployment direction, not an installed service.

Studio jobs/assets persist under ignored `logs/studio/` with SQLite and saved
files. Session state remains in memory while JSONL persists. ARC weights/outputs
and the external Unreal project are separate. Recoverable Trash retains files;
it does not free disk or delete engine maps.

The hosted planner key is separate from SSH/Slurm access. Strict SSH host checking,
scoped artifacts, bounded uploads, fixed native tools and filtered child environments
are local guardrails. Passwords, Duo and private keys stay in user-controlled
authentication tools. There is no app login, multi-user authorization or production
retention/security program. Keep sensitive trainee/patient/operational data out.

## Next acceptance checkpoints

1. Complete user-controlled SSH host/agent setup and update the ARC checkout.
2. Run one real couch through the frontend, retain the actual scheduler evidence
   and inspect the returned model and preparation result.
3. Execute the generic import in Unreal 5.8; verify materials, size, hull count,
   collision cooking and bounded contact behavior.
4. Verify the first live recorded movement clip.
5. Extend reviewed mixed-furniture IDs, footprint checks and Blender/Unreal bindings
   together, then review one complete room end to end.

## Review questions

Does each screen distinguish a request, running job, returned model, prepared
candidate and engine-verified result? Is the whole-result review useful? Which
environment and furniture combinations matter most for the next bounded proof?
What domain evidence would be needed before any training-effectiveness claim?

## Further reading

- [Current evidence](../current-status.md) and [documentation index](../README.md)
- [Asset setup/runbook](../asset-automation-runbook.md)
- [Room studio](../studio-pipeline-runbook.md)
- [Roadmap](../roadmap.md), [gap map](../full-system-gap-map.md), [full vision](../full-project-vision.md)
- [Security boundary](../security/README.md)
