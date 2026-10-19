# Batch history, duplicates and new assets — 2026-10-18

## Implemented: storage and deletion

Batches persist in the local workspace across backend restarts. Each sidebar entry now has a Delete icon; the selected batch also has a Delete this batch action. Delete moves the record to recoverable Trash and hides it from Recent batches. Restore returns the same batch with its layouts, worker outputs and recording links.

This is soft deletion: saved files remain on disk. It does not free storage, permanently erase data or delete maps/materials already created inside the separate Unreal project. There is no permanent-delete/empty-trash button in this batch. Active planning, application workers and video encoding must finish before deletion. Artifact/action routes reject trashed batches until restored.

## Implemented: duplicate handling

A request matches when its prompt, requested layout count, seed and model match. Prompt comparison normalizes Unicode, Windows line endings and leading/trailing whitespace; it is not a semantic similarity check. Different wording, punctuation, count, seed or model is a distinct request.

The frontend checks for a match without calling ARC. If one exists, the main button becomes Open existing batch. A checkbox explicitly permits asking ARC for a fresh plan instead. Backend duplicate detection runs under the same submission lock, so repeated clicks/concurrent identical requests share an existing queued/running job rather than starting multiple model calls. Completed batches are also reused. Failed, interrupted, trashed or missing-package batches are not reuse candidates. Older compatible saved batches work without manual migration.

Rebuild with seed remains the way to vary layouts from an existing plan without another LLM call. Replays now clear all copied downstream worker/output pointers; a new layout job must not claim the original job's Blender/Unreal/video outputs.

Validation: full backend tests, frontend build/lint and browser flow for duplicate reuse, explicit fresh requests, delete/restore and mobile Trash access. Tests verify concurrent identical submissions make one planner call, active deletion is rejected, files remain after deletion, trashed artifacts are unavailable, restore preserves outputs and replay does not inherit old application evidence.

## Proposed next batch: reusable asset library (not implemented)

The current generator supports only the prepared wooden chair. A couch or other requested furniture is currently rejected as unsupported rather than silently replaced with a chair. ARC LLM planning and ARC GPU asset generation are different services; the hosted LLM key alone does not submit a GPU job.

Start with one couch through the established Hunyuan lane:

1. Extract furniture needs from the natural-language brief. Look up a compatible reviewed asset first.
2. When missing, create a visible asset request. Obtain an input image from an upload or a separately verified image-generation route; Hunyuan's current pipeline is image-to-3D.
3. Run shape/texturing on ARC, using the approved allocation. Direct frontend submission requires a configured ARC connection/job adapter; that is not provided by the existing LLM API key.
4. Prepare the result in Blender: inspect appearance, repair obvious defects, establish dimensions/orientation/pivot, simplify geometry and create suitable collision shapes. New asset types cannot inherit the chair's 19-piece collision template blindly.
5. Review and register the asset with an ID, previews, files, dimensions, provenance and physics assumptions. Reuse it across subsequent room batches.
6. Extend the scene plan/layout contract, Blender assembly and Unreal import/binding together so mixed furniture footprints and asset IDs are handled consistently.

A couch should be generated/reviewed once and instanced many times. Regeneration should be explicit when a different appearance is requested. Room-plan caches must include the asset-library/contract revision once the single-chair schema changes. Do not label missing assets as ready or assemble substitutes without disclosing them.

First acceptance target: a prompt asking for a room with a couch and chairs uses the registered chair, creates or reuses a couch asset, lays out both using their actual recorded dimensions, assembles them in Blender/Unreal, and records a visual test. New asset generation/repair, generalized physics properties and this mixed-asset workflow remain proposed work requiring the next batch approval.
