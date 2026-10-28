# Generated-asset pipeline

The repository now has real chair generation evidence and an implemented
description-based asset lane. [Current status](../current-status.md) distinguishes
the accepted chair, native fixture checks and unrun automated couch.

```text
description + target dimensions + seed
  -> pinned SDXL reference on an allocated ARC GPU
  -> Hunyuan shape -> paint
  -> bound package, request/model/reference hashes and scheduler evidence
  -> local asset library and actual GLB review
  -> Blender MCP: preserved source -> conservative cleanup -> convex proxies
  -> packed editable .blend + preview + FBX/textures/UCX/import package
  -> visual review -> actual Unreal import/cooking/behavior check
  -> reviewed binding for reuse, when its downstream contract supports it
```

Hunyuan remains image-conditioned. Text drives a real generated reference in the
automatic lane; it is metadata in the optional manual-image route. Reference
generation is an internal intermediate, not a requirement to supply pictures.

## Preparation and review

The backend owns verified SSH transport and saved dispatch recovery. A real stdio
MCP server exposes only scoped `inspect_asset` and `prepare_asset` tools. It runs
fixed scripts, not arbitrary generated code or an open remote Blender socket.

Blender preserves imported source objects, minimally welds/dissolves/recalculates
the working copy, scales uniformly by target height and centers/grounds it. CPU
CoACD creates bounded convex proxies, which are checked and named for UCX export.
Actual dimensions, material limitations and FBX roundtrip evidence are reported.
The process cannot invent missing legs or reliably reopen arbitrary fused geometry.

The `.blend` is editable source; Unreal uses FBX and explicit textures/collision.
Generic package checks are not engine cooking evidence. Provenance checks bind
files to requests; they are not independent proof of visual quality or licensing
suitability. Retain source notices and human review decisions.

## Storage and room integration

Current library artifacts live under ignored `logs/studio/asset-library/` with
SQLite records. ARC binaries/models/outputs stay in project storage. The asset
folders in Git contain review guidance, not the full binary library.

The reviewed wooden chair is the existing room/Chaos binding. New chair/couch
designs remain review candidates and do not enter room assembly automatically.
Mixed-furniture IDs, footprints, registry revision, Blender instances and Unreal
bindings must be extended together.

- [Automation runbook](../asset-automation-runbook.md)
- [Manual variant route](../furniture-variants-runbook.md)
- [Review workflow](../../assets/metadata/asset-review-workflow.md)
- [Blender checklist](../../assets/metadata/blender-review-checklist.md)
- [Object contract](environment-object-contract.md)
