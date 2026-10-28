> **Historical checkpoint/plan:** retained as written for its date. For current implementation, evidence and setup, use [current status](current-status.md) and the [documentation index](README.md). Old branch, approval and next-action instructions below may be superseded.

# Current project handoff — October 18 evening / October 19 UTC, 2026

**Newer checkpoint:** `docs/arc-handoff-2026-10-26.md` records the implemented
asset-automation and Blender MCP batch, actual native checks and remaining SSH
setup/live-run boundary. The October 19 plan-only statements below are history.

## October 19 resumed direction — supersedes the manual next action below

Andy resumed and requested resolution of all seven open PRs before moving ahead.
All seven PRs (#1–#7) were merged into `main`, preserving their history; none
remains open. The final stack merge is `0a0535b`. Use `main` as the baseline;
older branch instructions below are historical. Each PR passed its GitHub checks
before merging. Final local validation: 118 backend/ARC tests, frontend build/lint,
repository Ruff, Python compilation, Bash syntax and JSON checks pass; npm audit
reports zero vulnerabilities. New CI covers frontend checks and ARC tests as well
as backend checks. No new GPU or Unreal runtime was executed during resolution.

The local app saved couch request
`64e106d0434281a2a919e2d7e7706dd8a17d18f48b5f9be767a185fa7a55ce52`
(1.8 x 0.85 x 0.85 m, seed 42); its ZIP was validated. No GPU submission occurred.
Andy prefers testing natural-language asset creation and frontend ARC submission
before the manual couch run. See `docs/asset-automation-plan.md` for the bounded
next batch and its unresolved image-provider/SSH setup prerequisites. The plan is
documented; neither automated image generation nor SSH transport is implemented.

PR resolution also fixes the original Unreal setup's tilted axis, stable LF
script bytes/helper hash, and retryable Blender asset-worker failure handling.
Offline tests do not constitute a new engine or GPU runtime observation.

**Resume here.** This replaces older handoffs as the current starting point while preserving them as history. Andy asked to stop with the work saved, checked and documented. No further work or model calls should start automatically while paused.

## Goal and working style

Build a visually verifiable emergency-training proof of concept for Dr. Cameron: a natural-language prompt becomes scenario plans; VT ARC supplies large-model compute; assets are prepared in Blender; Unreal Engine/Chaos assembles and simulates rooms; the frontend controls work and displays evidence. Andy is a beginner and prefers simple explanations, scripts, one whole-result review and batch approvals. Prioritize demonstrable visuals over more deterministic-backend scaffolding. Do not request credentials in chat.

## What actually works

| Part | Current evidence/status |
| --- | --- |
| ARC Hunyuan chair shape | Job **8052814**, completed in 3m14s. Original geometry preserved. |
| ARC Hunyuan chair PBR textures | Job **8053348**, completed in 3m25s. Actual GLB/materials returned and inspected. |
| Blender chair preparation | Blender **5.1.2**; repaired visible gaps, reviewed model, floor pivot and **19** simple convex collision pieces; user accepted result. |
| Unreal chair demo | Unreal **5.8**; user confirmed upright/tilted drops, rocking and settling. Preserve working project. |
| ARC hosted natural-language planner | `gpt-oss-120b`; authenticated access and frontend scenario generation confirmed by user. |
| Frontend room planning | Saved plans, seeded layouts, previews/downloads and persistent jobs. Current contract supports the reviewed wooden chair only. |
| Local Blender room worker | User confirmed frontend batch assembly works. New file/preview, source chair preserved. |
| Unreal editor bridge | User connected it manually once; frontend populated maps. One bridge load per editor session, mesh binding reused. |
| Chaos room batches | User confirmed rooms cycle every **10 seconds** and observations download. Ground-level chairs may remain still. |
| Recorded movement demos | Implemented and tested with fake-editor protocol plus real local FFmpeg encoding. **First live Unreal screenshot/MP4 run has not been confirmed by user.** |
| Batch history/duplicates | Implemented; recoverable Delete/Trash/Restore; exact matching requests reuse existing jobs unless explicitly requesting a fresh plan. |
| New furniture variants | This approved batch adds saved chair/couch designs, portable ARC request/result packages, actual GLB viewing and background Blender staging. **First live couch run is still pending.** |

Playback observations are not calibrated physics, contact tests, evacuation validity or real-time browser streaming. Browser Rapier tools and the legacy deterministic backend remain separate from Unreal Chaos.

## Fixes completed along the way

- Repaired npm manifest/lock consistency, missing PhysicsLab source and React Three dependencies; fixed the backend PhysicsProofService constructor call.
- Fixed frontend focus decoration alignment and connected actionable pipeline controls.
- Diagnosed Windows ARC connectivity: DNS/TCP succeeded but Python did not trust the HTTPS certificate. Native Windows certificate verification through `truststore` fixed it; no TLS verification was disabled. The no-key diagnostic's HTTP401 is expected and establishes verified HTTPS, not key validity. User subsequently confirmed live generation works.
- Added the local editor bridge, persisted command/results and safe artifact routes. Model text is not executed as application code.
- Added saved recordings, run-specific observations, range-enabled MP4 downloads and encode retry from saved frames. A fixed movement-demo input is explicitly uncalibrated.
- Added batch Trash/Restore and concurrent duplicate suppression. Trash hides batches and keeps files; it does not free disk space or delete Unreal maps. A new replay clears inherited worker/output pointers.

## Current approved furniture batch

Andy approved the couch/reusable-library batch and clarified that multiple designs of one furniture type must be supported. A wooden dining chair, metal folding chair and upholstered armchair are separate variants; many instances of one design reuse one model.

Implemented files:

- `backend/app/studio/assets.py`, `backend/app/api/assets.py`, and router registration in `backend/app/main.py`.
- `web/src/AssetLibrary.tsx`, its CSS, and navigation from `SpatialWorkbench.tsx`.
- `arc/scripts/asset_request.py`: portable immutable request validation and hashes.
- `arc/scripts/hunyuan_variant.py`: request extraction and completed-result packaging.
- `arc/scripts/submit_hunyuan_variant.sh`, `arc/jobs/generate_hunyuan_variant.sbatch`: one GPU job runs the established shape and texture scripts, retains raw/intermediate outputs, then exports a generic `asset.glb` package.
- `scripts/blender/prepare_furniture_variant.py`: imports a returned GLB into a separate review file, preserves materials, packs textures, uniformly matches requested height and centers/grounds geometry. It reports actual staged dimensions. Orientation, pivot, topology and collision suitability remain review work.
- `backend/tests/test_asset_library.py`: identity/reuse, import matching, hashes, foreign origin, unsafe ZIP/resource rejection, exporter roundtrip, notices and worker credential boundaries.
- Prepared charcoal two-seat couch reference plus its image-generation prompt under `web/public/references/`. This is an image, not generated couch geometry. WebP is used for delivery; browser encodes PNG for the ARC request. The full generated source image is retained in this conversation.

Variant identity includes family, normalized name/description, target dimensions, image bytes, shape seed and pinned settings/model/source revisions. Matching is exact input identity, not semantic similarity. Changing any input creates another variant. Generated results are kept immutable; change seed/design for another attempt. Hunyuan consumes the reference image; the design description is metadata, not text conditioning. Upstream paint uses its defaults; saved results are reused rather than claiming bitwise regeneration.

Returned ZIPs must match the request and declared provenance/hashes. GLB resources must be embedded. Successful import is `generated_review_needed`, **not room-ready**. The frontend's 3D viewer displays the actual GLB; a preparation button produces `furniture-review.blend` and a size report using the configured local Blender executable.

**Important boundary:** room planning/Blender room assembly/Unreal still use the original wooden chair. Mixed-asset room contracts and bindings are not implemented. Do not silently substitute a chair for a couch, reuse the chair's 19-piece collision recipe for another design, or mark a new asset approved without inspection. The live couch mesh is needed to choose appropriate repairs/colliders.

## Checks completed for this checkpoint

- **108 backend tests pass** in the isolated tracked-source snapshot, including 10 new asset-library tests.
- `npm --prefix web run build` succeeds; asset viewer is lazy-loaded. Existing large-physics-chunk size advisory remains; it is not a build failure.
- `npm --prefix web run lint` and targeted Python syntax/error lint.
- Browser checks: save a couch request, download its ZIP, reopen exact duplicate without another design, reset reference when switching family, mobile navigation/no horizontal overflow and no page errors. Rechecked after web-reference encoding change.
- Actual pre-existing chair GLB displayed in the new browser 3D viewer without page errors, under an explicitly labeled local test fixture. **No synthetic couch or substitute production output was supplied.**
- Actual Blender **5.1.2** Python runtime executed the new staging script on the existing textured chair: saved a separate review `.blend`, retained materials and measured about **0.542 × 0.633 × 1.000 m** after uniform height matching. This checks the generic preparation path, not an unseen couch mesh or the Windows executable launch.
- ARC shell syntax and portable request extraction/export roundtrip pass. **New Slurm job execution on ARC has not run here.** Existing shape/paint environments were already confirmed by the user.

## Exact next action when resuming

Read **`docs/furniture-variants-runbook.md`** and guide Andy through the first couch run, one step at a time:

1. Update/restart the Windows app from `codex/arc-scenario-workspace`; frontend **Asset library → Save design request → Download ARC request**. Use the prepared couch defaults unless Andy changes the design.
2. On VPN/Open OnDemand, upload the request ZIP to the ARC home directory; update the ARC checkout to the same branch, preserving ignored settings.
3. From the ARC repo root run the frontend's displayed command, replacing its placeholder path with the uploaded file's actual path:

   ```bash
   bash arc/scripts/submit_hunyuan_variant.sh "$HOME/asset-request-ACTUAL_SHORT_ID.zip"
   ```

4. Record the submitted job number. Check `sacct` and the `arc/results/hunyuan-variant-JOB_ID.{out,err}` logs. The success log prints the exact `result.zip` path under project storage.
5. Download that ZIP through Open OnDemand, import it into the selected frontend asset card and inspect the actual generated couch.
6. Run **Prepare Blender review copy**, inspect its orientation/shape/materials and actual dimensions. Only then prepare collision pieces and implement mixed-variant room placement/bindings as the next concrete batch.

No new model/environment build should be needed. No hosted LLM API key is required for this GPU job. No direct ARC SSH/job connection is configured in the backend; this remains an explicit upload/submit/download route. The backend does not know remote scheduler state. Do not say the couch is generating until Andy provides a submitted job number.

Separately, verify the first actual recorded Unreal clips using `docs/visual-playback-runbook.md`. Keep the existing working Chaos run as the baseline.

## Environment and private configuration

- Repository: `Andy71517/emergency-training-poc`. Active working branch **`codex/arc-scenario-workspace`**, draft PR **#7**. Stacked prior PRs remain unmerged. Do not merge automatically.
- Windows checkout: `C:\Users\aniru\Desktop\GitHub\emergency-training-studio`; Python3.12 `.venv`, Blender5.1.2, Unreal5.8.
- Private `backend/.env`: `ARC_LLM_API_KEY`, `ARC_LLM_MODEL=gpt-oss-120b`, `BLENDER_EXECUTABLE`, `CHAIR_BLEND`. Existing settings must not be overwritten. Never print/send keys. Later institutional key/quota arrangement with Dr. Cameron remains a user-side decision.
- Backend command: `.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8765`. Single local process; frontend at `http://127.0.0.1:8765`. Do not expose this unauthenticated single-user POC publicly.
- New batches/assets persist under ignored `logs/studio/`, including SQLite, generated files, worker evidence and recordings. Scenario deletion does not delete reusable assets.
- Blender can run in the background from its executable; it need not be open. Unreal must remain open for editor bridge/Chaos operations. Saved renders/clips can be viewed without either application open. No live editor stream is implemented.
- ARC shell: `tinkercliffs2`; repo `/home/anirudhalledula/emergency-training-poc`; project workspace `/projects/research-mel/anirudhalledula/emergency-training-poc`.
- Slurm: account **`research-mel`** (hyphen), partition **`a100_normal_q`**, QoS **`tc_a100_normal_base`**. Use ignored `arc/.env`; do not commit or paste it.
- Existing Hunyuan root `$ARC_PROJECT_WORKSPACE/hunyuan21`, separate shape/texture Conda environments; existing Apptainer container and A10080GB. New runs live under `hunyuan21/variants/FULL_ASSET_ID/run-JOB_ID/`; completed reusable ZIP at `variants/FULL_ASSET_ID/result.zip`.
- TRELLIS runtime was built successfully, but generation remains paused on DINOv3's access gate. Last user report: access not granted. Keep this lane open without resubmitting or changing authentication blindly.

## Further work, after the first couch

- Review actual couch quality and prepare suitable convex collision pieces; do not claim arbitrary automated repair is solved.
- Extend planner schema, asset lookup, layout footprint checks, Blender assembly and Unreal mesh/material binding together. Include library/contract revision in future scenario cache keys.
- Resolve natural-language furniture requests against reviewed variants and show missing designs as requests; add explicit generation choices rather than silent replacements.
- Validate first real MP4 capture and improve framing/smoothness from evidence.
- Add physically meaningful measurements when useful; current inputs/material values are demonstration assumptions.
- Permanent disk cleanup, automatic remote job transport, institutional deployment, agents/smoke/navigation and live streaming remain later work.

Suggested next-chat instruction: **“Resume from docs/arc-handoff-2026-10-19.md. Let's submit the first couch request.”**
