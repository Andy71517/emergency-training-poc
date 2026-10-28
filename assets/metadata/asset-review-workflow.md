# Asset review workflow

The reviewed wooden chair is the current room baseline. New designs produced by
the [asset workflow](../../docs/asset-automation-runbook.md) remain candidates.
Automatic preparation is useful evidence, not automatic promotion.

## 1. Generate or collect a candidate

Use a description-driven ARC dispatch or the optional manual reference/package
route. Current app files live under ignored `logs/studio/asset-library/`; ARC files
stay in project storage. `assets/generated/` is optional local staging, not the registry.
Keep the original GLB and generation lineage immutable.

## 2. Record provenance

Keep request/description/reference identity, model/source revisions, seed/settings,
Slurm evidence, returned file hashes and notices. Use the
[metadata template](asset-review-template.md) for the human decision and limitations.
Hashes bind a package to a request; they do not decide licensing suitability or quality.

## 3. Prepare and inspect in Blender

The scoped MCP worker preserves source objects, cleans a copy conservatively,
uniformly matches height, grounds/centers, creates convex proxies and exports an
editable `.blend` plus Unreal package. Inspect the whole result using the
[checklist](blender-review-checklist.md): shape, missing/fused parts, orientation,
actual dimensions, pivot/floor contact, UVs/materials and collision coverage/gaps.
Automated cleanup cannot reconstruct arbitrary missing geometry.

## 4. Validate the intended engine use

Unreal imports FBX/textures/UCX, not `.blend` directly. Verify the actual material
binding, size, hull count and collision cooking in the target engine, then inspect
bounded contact/stability behavior. The generic importer still needs its first
live acceptance check; chair-baseline evidence does not cover a new couch.

## 5. Record a human decision

Use an explicit decision such as candidate, needs changes, reviewed visual only,
reviewed collision candidate or rejected. Record exact revision/checksums, reviewer,
intended use and unresolved limits. These review labels are guidance, not a claim
that the app automatically publishes or approves new assets.

## 6. Bind for reuse only when supported

Current room workers use the reviewed chair. Mixed furniture requires coordinated
planner IDs, asset lookup/footprints, Blender instances and Unreal bindings. A
prepared design is not room-compatible merely because its ZIP exists. Optional
promotion into `assets/reviewed/` does not change the application's registry.

Reviewed means a bounded POC quality decision, not clinical, operational, physical
or training certification. [Current status](../../docs/current-status.md).
