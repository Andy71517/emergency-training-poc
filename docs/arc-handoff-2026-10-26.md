# Asset automation and Blender MCP â€” October 26, 2026

## Current batch

Andy approved implementation of natural-language asset generation, backend-owned
ARC submission/retrieval, and Blender MCP cleanup/collision/export. The seven
earlier PRs remain merged. This is a local single-user POC; no remote credentials
were created, collected or changed. Preserve the working chair rooms and evidence.

Implemented:

- Asset library **Describe it. Build it.**, connection check, persistent dispatch
  progress, same-job resume and generated-design links. Manual image/ZIP route is
  retained as an explicit alternative. Unsupported designs are not replaced by chairs.
- Pinned SDXL 1.0 reference generation on ARC using the existing shape environment,
  followed by the verified Hunyuan shape and paint scripts in one Slurm job. Public
  model revision/access was checked. First actual SDXL import/inference in that
  ARC environment remains unexecuted. No new runtime build is claimed.
- Fixed SSH RPC using BatchMode and strict host checking; bounded transport,
  persisted dispatch journal, scheduler comment recovery, no blind resubmission,
  exact prompt/model/reference/job/result binding and preserved notices.
- Real MCP stdio client/server with `inspect_asset` and `prepare_asset`, scoped to
  saved library IDs. No arbitrary code execution or remote Blender socket add-on.
- Background Blender cleanup of a preserved-source copy, height matching/floor
  pivot, isolated CPU CoACD decomposition (2 cm threshold, <=32 hulls/64 vertices),
  convex/closure/volume/bounds checks and named UCX pieces. Cleanup removes
  collapsed/coincident geometry; it does not reconstruct arbitrary missing/fused parts.
- Packed editable `.blend`, rendered preview, FBX with explicit textures/material
  factors, provenance, hashes and a generic Unreal 5.8 import helper. FBX roundtrip
  checks count, bounds, material slots and UV layers. Temporary reimport images
  are removed so they cannot break texture packing.

## Verified here

- **138 backend/ARC tests pass**, including real MCP handshake/tool schema,
  submission uncertainty/recovery, duplicate suppression, credential/origin/path
  boundaries, worker retry behavior and Unreal package preflight.
- Frontend production build and ESLint pass; browser preview shows the description
  form, disabled setup gates and no horizontal overflow/page errors. Repository
  Ruff, Python compilation, ARC Bash syntax, JSON and pip consistency checks pass.
- Real Blender **5.1.2**, real MCP call and real CoACD ran on an explicitly
  synthetic box-furniture fixture. It generated **28** closed convex proxies,
  saved/reopened a packed Blender file with its eight original source objects
  preserved, and passed an FBX roundtrip with **29 meshes**, one material slot and
  one UV layer. The output dimensions 1.530 x .680 x .850 m correctly triggered the
  requested-size mismatch flag. This is test machinery evidence, not a generated couch.
- Actual native ZIP/hash/material preflight checks passed. The generic Unreal
  importer has compile/preflight checks only; engine APIs, materials and collision
  cooking have not run during this batch.

## Actual blocker and resume

The read-only SSH check returned **No ED25519 host key is known ... Host key
verification failed**. No host trust or credential setup was changed. Follow
`docs/asset-automation-runbook.md` for user-controlled host verification,
passphrase-protected key/agent setup, updating the ARC checkout and setting
`ARC_SSH_TARGET`/`ARC_REMOTE_REPO` in the private local backend configuration.

Only after the app connection check succeeds should the first actual couch job
start. No couch GPU job or result exists at this checkpoint. The old reference
request `64e106d0434281a2a919e2d7e7706dd8a17d18f48b5f9be767a185fa7a55ce52`
remains a baseline; the automated run must generate a real reference from the new
prompt and retain its lineage.

First review: actual couch GLB, staged dimensions, cleanup report, collision fit
and the entire prepared Blender result. Then run the bundled importer in Unreal
5.8 and inspect materials, hull count, size, collision cooking and contact behavior.
No calibrated physics or structural suitability is inferred from appearance.

Mixed-asset room planning/footprints and Blender/Unreal bindings remain a
coordinated follow-up: existing room demos still use the reviewed chair. This
batch implements the requested asset-automation lane, not arbitrary whole-room
semantic repair or a validated emergency/evacuation simulation.
