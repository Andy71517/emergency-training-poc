# ARC visual POC handoff — 2026-10-18

## Verified today

- Andy switched to Hunyuan branch `codex/arc-hunyuan-chair` at `89c95a9` and confirmed the shape config/checkpoint were accessible without a token.
- Build job `8052562` completed in 7m48s, exit `0:0`. Logs show no broken requirements, PyTorch `2.5.1+cu124`, NVIDIA A100-SXM4-80GB, and `Hunyuan shape imports and CUDA: OK`.
- Shape job `8052814` completed in 3m14s, exit `0:0`. It downloaded/loaded the model, removed the background, generated shape, exported GLB/PLY, and rendered the preview.
- Raw result directory: `/projects/research-mel/anirudhalledula/emergency-training-poc/hunyuan21/outputs/wooden-chair-8052814`. Andy uploaded the preview, turntable, original GLB, and manifest for inspection. The GLB is about 4.7 MB. Counts match the manifest: 134,104 vertices, 268,228 triangles.
- Visual review across eight turntable angles: recognisable chair with seat, four legs, backrest and crossbars. Backrest slat gaps appear partly filled; surface triangle/noise artifacts require judging the original mesh in Blender.
- Direct GLB audit: consistent winding, finite coordinates, no duplicate faces, no boundary edges, four nonmanifold edges caused by four collapsed triangles. Removing those four in memory yields a watertight mesh, consistent winding, unchanged bounds, and 268,224 triangles. The uploaded raw file was not changed. Self-intersections and physical suitability have not been fully validated. No textures or UVs were present. Physical scale and collision are unverified.

## Approved next batch

Andy approved preserving the raw asset, cleaning a working copy, and adding Hunyuan texture generation on ARC. The prepared branch is `codex/arc-hunyuan-textures`, based on the Hunyuan geometry branch. It adds an isolated paint environment/build, small access checks, recorded source fixes, cleanup plus a reduced UV/paint working copy, explicit PBR GLB export, and a base-color turntable. The original full-resolution cleaned GLB is kept separately from the reduced textured copy. Read `docs/arc-hunyuan-texture-runbook.md` for the exact commands and expected outputs.

Local validation includes cleanup on the actual uploaded chair (four faces removed, closed mesh, source hash unchanged) and a material fixture export/reload verifying embedded color, UVs, roughness in G, and metallic in B. ARC texture compilation and inference have not yet run. Do not call the textured lane complete until actual files have been returned and inspected.

## Resume

1. Fetch/switch to `codex/arc-hunyuan-textures` in the existing ARC checkout; keep `arc/.env` private.
2. Run texture access checks, submit `bash arc/scripts/submit_hunyuan_texture.sh build`, and verify its final state and import/CUDA log.
3. Submit `bash arc/scripts/submit_hunyuan_texture.sh paint 8052814`. Inspect its preview, GLB, maps and manifest. Preserve intermediate outputs if only the preview fails.
4. After texture review: Blender scale/orientation/topology cleanup and collision preparation, then Unreal Chaos demonstration. These stages remain pending.
5. TRELLIS remains available on its existing branch/runtime. The last reported DINOv3 request is still pending; do not resubmit TRELLIS until access and private authentication are verified.

The latest prior handoffs are `docs/arc-handoff-2026-09-28.md` and `docs/arc-handoff-2026-10-04.md`. Draft PRs #1 (browser visual physics), #2 (TRELLIS), and #3 (Hunyuan geometry) remain separate; no merge was performed in this session.

## Texture build follow-up

Texture build job `8052986` failed after 9m30s. Python dependency installation, the custom CUDA rasterizer build/install, and the silent C++ helper step completed; `pip check` rejected `ninja 1.11.1.1` as unsupported on the platform before the final import/CUDA check ran. Updated the texture-only Ninja pin to `1.11.1.4`, whose wheel uses valid modern platform-tag metadata. Fetch this branch and rerun the texture build, reusing the existing environment and caches. Texture runtime and paint inference remain unverified until that retry succeeds.

## Texture import follow-up

Retry build `8053061` completed in 1m43s, exit `0:0`, with `Hunyuan texture imports and CUDA: OK`. Paint job `8053186` then failed in 2m29s after successful cleanup (four faces removed, watertight working copy), weight downloads, and main pipeline component loading. The error was `ModuleNotFoundError: pytorch_lightning`, reached through `hunyuanpaintpbr.__init__` importing its `HunyuanPaint` class. Added upstream-pinned `pytorch-lightning==1.9.5` and `torchmetrics==1.6.0`, and extended the build smoke check to import `Dino_v2` through that same package. Dependency resolution and Bash syntax pass locally; actual ARC import verification is pending the build retry. Pull the texture branch, rerun its build, then paint original shape run `8052814` after verification. Downloaded model weights remain cached.

## Later update — texture success and Blender checkpoint

- Texture build 8052986 failed because ninja 1.11.1.1 wheel metadata was unsupported; pin 1.11.1.4 fixed it. Build 8053061 succeeded. Paint 8053186 exposed an upstream Lightning import missing from requirements; added pytorch-lightning 1.9.5 / torchmetrics 1.6.0 and strengthened smoke import. Build 8053321 succeeded in 49 seconds.
- Paint **8053348 completed successfully** in 3m25s, exit 0:0. Output: `/projects/research-mel/anirudhalledula/emergency-training-poc/hunyuan21/outputs/wooden-chair-textured-8053348`. User returned GLB, manifest, still and turntable. Embedded 1024-square albedo/metallic-roughness textures, valid UVs, 80,000 triangles / 49,933 UV-split vertices; welding positions for analysis yields one closed, consistently wound component. Raw source preserved per manifest. Preview is simplified base-color shading, not full PBR rendering.
- Andy approved Blender preparation, using Blender 5.1.2 locally. Imported GLB, saved `chair-working.blend`, scaled uniformly by .503, applied scale; dimensions .542 x .633 x 1 m. This is an assumed demo size. Manual origin placement left bottom Z=-.02656865; script corrects exactly.
- Solid/Edit Mode screenshots confirmed filled backrest gaps are geometry, not just texture. Andy uploaded `chair-cleanup.blend`; preserve it. New stacked branch `codex/blender-chair-prep` contains the tested, specific repair preview script and `docs/blender-chair-repair-runbook.md`.
- Test on uploaded file in official bpy 5.1.2: five live Boolean gap cuts, copied material with neutral remnants tinted brown, source hidden/preserved. Evaluated 72,664 triangles, zero nonmanifold edges, floor min Z=0; source geometry/UV/albedo unchanged. Front/rear Cycles renders inspected. Visual repair still needs Andy's local review; no collision, Unreal export or physical test completed yet.

Resume at `docs/blender-chair-repair-runbook.md`: run repair script in Scripting workspace, review result, save a separate preview, then continue approved Blender batch with material review, foot contact, simple convex collisions and Unreal export. TRELLIS remains paused pending DINOv3 access.


## Automated collision completion — later October 18

Andy ran the backrest repair successfully and returned front/side screenshots. He saved chair-repaired-preview.blend, then chair-collision.blend. Manual seat and four leg UBX pieces were entered and reviewed; backrest collider was not started. Andy requested replacing the per-object screenshot workflow with one tested script and one whole-result review.

Uploaded chair-collision.blend inspected in official bpy 5.1.2. Added scripts/blender/complete_hunyuan_chair_collisions.py and docs/blender-chair-collision-runbook.md on the existing Batch 5 branch. It preserves and hides SM_Chair and the manual UBX pieces; creates evaluated SM_Chair_Demo and 19 closed convex UCX colliders, with separate slats/open gaps and flat proxy feet at Z=0. Original geometry, transforms, UVs and packed texture pixels unchanged. Fifteen gap-ray samples and one under-chair sample clear; front/rear QA renders inspected. Saved/reopened output verified; repeat execution rejected. Chaos cooking, material setup in Unreal, mass/friction and stability remain untested.

Delivered separate completed copy chair-collision-complete.blend (script already run) and the reusable script. User can open the prepared file OR run script on original input, not both. Resume with one visual review of whole collision set, then automated selective Unreal export. No need to resume manual backrest-box instructions. New collection POC_Complete_Collision_Preview is the export candidate; original UBX/cutters must be excluded. The report is a Text datablock named POC_collision_report.json.


## Collision review accepted; Unreal export prepared

Andy inspected the complete 19-piece collision preview and said it looks good. Prepared scripts/blender/export_hunyuan_chair_unreal.py plus docs/blender-chair-unreal-export-runbook.md. Delivered chair-unreal-export.zip (FBX, three PNG maps, explicit two-slot material plan, reports/provenance). Exporter works in a temporary scene and does not modify/save the source. It excludes manual UBX backups and Boolean cutters, exporting one render mesh plus 19 matching UCX hulls only. Three textures are explicit because FBX material conversion does not establish Unreal PBR wiring.

Verified Blender 5.1.2 FBX export/reimport roundtrip: 20 meshes, 19 hulls, 72,664 render triangles, two used slots with matching assignments, active UVs and bounds preserved within 1e-5 m. Roughness and metallic PNGs match packed G/B channels exactly when reloaded as data. Source object set, geometry/transforms/hide flags/UVs/packed pixels unchanged; existing-folder guard passes. Compilation/Ruff and ZIP integrity pass. FBX version 7400. No Unreal import/cooking/Chaos run yet.

Resume: Andy downloads/extracts the ZIP; obtain installed Unreal version (or installation status) before exact import steps/Editor Python setup. Verify ~100 cm height, Z-up/floor pivot, 19 simple hulls and explicit material mapping inside Unreal, then build and record the drop/tip demo. No need to rerun Blender export if using the prepared package.


## Unreal version confirmed: 5.8 — setup script prepared

Andy confirmed Unreal Engine 5.8. New stacked branch codex/unreal58-chair-demo contains unreal/scripts/setup_unreal58_chair_demo.py and docs/unreal58-chair-demo-runbook.md. Delivered chair-unreal58-demo-setup.zip with the previously verified FBX/maps plus script and START-HERE instructions, all in one folder.

Script intended behavior: verify package hashes and clean saved current map; create a unique content folder and separate lit map; temporarily select legacy FBX import and restore the feature flag; require 19 convex hulls and approximately 100 cm height/floor pivot; wire two chair materials explicitly; create a floor, camera, display chair, upright drop and tilted drop. Dynamic settings (5 kg, .55 friction, .05 restitution) are demo assumptions. Script does not start simulation; user inspects then Alt+S, Esc to stop. Reports success/failure in project Saved/EmergencyPOC.

Validation completed here: API references checked against Epic docs, Python compile/lint, valid-package preflight, missing/altered texture rejection, and ZIP integrity. IMPORTANT: no Unreal runtime is present here. No UE imports, API property calls, shader compilation, collision cooking, map creation or Chaos simulation have been executed. First run on Andy's PC is the integration check. Do not overstate validation.

Resume: create/open a separate Blank Blueprint project in 5.8; enable Python Editor Script Plugin and restart; save current map; File > Execute Python Script selects bundled setup_unreal58_chair_demo.py. Inspect whole scene once; return screenshot/observed drop behavior or first error/report. Do not resume manual collider entry. The Blender/export PR remains stacked and unmerged.


## Unreal runtime observed; presentation batch approved

On October 18, Andy ran the original setup successfully in Unreal Engine 5.8. Returned screenshots show the textured three-chair level, lights/floor/camera, then the chairs resting during simulation. Andy explicitly reported: “the chairs fall and settle on the floor, within a second or two.” This is user-observed basic gravity/contact/settling success. It is not an instrumented physics benchmark or evidence of calibrated mass/friction. No emergency room/scenario has been constructed yet.

Andy approved a presentation batch. Added unreal/scripts/prepare_unreal58_chair_presentation.py and docs/unreal58-chair-presentation-runbook.md. Delivered chair-unreal58-presentation.zip with this script and its hash-checked original setup helper; no models/maps/textures need downloading again. Run with the saved original L_ChairVisualDemo open and simulation stopped. The script validates original actor labels/shared mesh/19 hulls/material references, then creates a unique separate presentation map using existing assets. Shared source assets and baseline map are not modified. Adds front-facing framing, fixed reference/upright/tilted labels, title/pipeline text and provisional-physics note. Initial pivot heights become 0/100/120 cm, tilted roll30 degrees, all yaw180 degrees. Original assumed physical values remain. No automatic simulation or video capture; normal project time settings. Alt+S/Esc provide repeatable start/reset; record a three-second initial hold plus eight seconds of simulation using screen capture.

Validation here: Python compilation/Ruff py311, helper loading without Unreal side effects, correct-helper acceptance and missing/tampered-helper rejection, ZIP integrity. The original scene has actual user runtime evidence; the NEW presentation script has not run in Unreal here and awaits Andy's whole-scene review. Report path Saved/EmergencyPOC/chair-presentation-*.json. Partial new map may remain after failure; original remains available. Resume with one execution/review, then a short recorded clip for Dr. Cameron. After preserving that evidence, propose a separate batch for a small room and emergency scenario. TRELLIS remains paused pending DINOv3 access. Existing stacked PRs remain unmerged.


## Presentation rotation correction

First presentation screenshot shows inverted chairs. Positional Rotator argument ordering caused unintended pitch180 instead of yaw180. Replaced presentation rotations with explicit pitch/yaw/roll keywords and text colors with named RGBA channels. First original setup's nominal tilted case used yaw30, so earlier observed drop success does not establish a 30-degree tilted condition. Corrected presentation explicitly sets roll30. User must reopen original ChairDemo map, then execute revised presentation script to make a fresh map; press G to hide text/light billboards. Revised presentation runtime awaits review.


## Chair presentation accepted; prompt-to-scene next

Direct component repair v3 succeeded on Andy's PC. He confirmed properly oriented chairs and tilted chair falling, rocking, then settling upright. Returned 11.5145-second Unreal video reviewed via sampled frames: initial raised state, drops, settled chairs and stationary reference. Preserve current project as working baseline. Do not resume inverted presentation rebuilds; use v3 repair if necessary. New corrected scene generation must set component transforms and verify readback.

Andy clarified the intended scope: natural-language authored scenes produced through ARC, assembled/reviewed in Blender, then simulated in Unreal; not merely manual Unreal room construction. He approved investigating and preparing that batch. See docs/prompt-to-scene-batch-plan.md for exact scope, contracts, reuse strategy and boundaries. Official ARC documentation confirms hosted chat-completions endpoint and user-created personal keys; user authentication unverified. Added small stdlib arc/scripts/check_scenario_planner_access.py, hidden prompt, no key persistence/response dumps. First next step: Andy privately creates/reuses key at llm.arc.vt.edu and runs access checker on ARC. No new GPU installation/sbatch required for this small API check. Never ask him to paste credentials in chat.

Only proposal and access checker prepared at this checkpoint: spatial schema, real prompt planner, seeded variants, Blender assembler, Unreal room assembler and fresh-asset resolver are not yet implemented. Existing authoring API remains a mock; preserve deterministic runtime authority. No room-level scenarios have run. Reuse reviewed chair for first three variants; expand to fresh assets after shared-contract assembly works. No further approval is needed to continue the already approved scoped implementation; obtain actual endpoint status before claiming live planning works.


## ARC model access confirmed; first real prompt-to-plan generator prepared

Andy ran the access checker successfully: endpoint reachable, authenticated gpt-oss-120b response received. Earlier HTTP400 cause remains unknown; sanitized diagnostics were added, and the next request succeeded. Do not attribute a specific cause.

Added arc/scripts/generate_scenario_batch.py, arc/tests/test_scenario_batch.py and docs/arc-scenario-batch-runbook.md. CLI calls the hosted model with a bounded room-plan contract, validates its actual final JSON, expands saved plan into seeded layouts, validates containment/non-overlap/designated-aisle conditions and writes JSON/SVG/HTML review package plus hashes. Default request: three classroom-like chair layouts, two clear aisles and one obstructed. Count1-30 supported; only reviewed chair asset supported. Private key hidden/not persisted; API diagnostics sanitized. Replay mode requires saved plan and calls no model. No fixture fallback for failed live calls.

Offline tests pass: invalid plans, duplicate/nonfinite JSON rejection, 540 layout combinations, over-capacity rejection, repeatable spatial scene replay, package hashes/no-overwrite. Compilation/lint pass. Preview markup generated from explicitly offline fixture; no model-generated layouts have yet been returned. No live request can be made here without Andy's private runtime key. First next command on ARC after git pull: python3 arc/scripts/generate_scenario_batch.py. No sbatch/model build required. Return plan.json, manifest.json and preview screenshot.

Output stage spatial_drafts_ready, human review required. Registry currently records chair identity/dimensions/provenance only: binary binding and hashes remain future work. Blender/Unreal room consumers are not implemented by this checkpoint; proceed after inspecting actual model interpretation. Aisle overlap is not full pathfinding, impassable exit proof or evacuation simulation. No new assets generated. Existing backend/mock authoring unchanged. See runbook for exact commands/replay/count/custom prompt and limitations.


## First ARC spatial plans returned; Blender rooms assembled

ARC generator run succeeded in /home/anirudhalledula/emergency-training-poc/arc/results/scenario-batches/20261019_003044_818369. Andy returned plan.json and manifest.json. Plan:8x8x3m,1.2m doorway,1.6m aisle,12 chairs,clear/clear/obstructed. Canonical plan digest and plan file digest match. Rebuilt room JSON at seeds20261018/19/20; all three SHA256 hashes exactly match ARC manifest. Thus no new LLM/ARC run is required to assemble these exact rooms. The model returned the example's values; real prompt adaptation has not yet been demonstrated. request.json/raw model response not supplied.

Added scripts/blender/assemble_scenario_rooms.py and docs/blender-scenario-room-runbook.md. Ran actual Blender5.1.2 assembly from previously reviewed chair-collision-complete.blend. New separate file has three individual metre-coordinate scenes plus a side-by-side overview using collection instances. Physical room meshes include 1.2x2.1m doorway openings; front walls hidden for cutaway review; no ceilings. Green aisle/red obstruction guides are annotations.36 chair instances,684 hidden convex collider instances; packed chair materials; 12 chairs per room. Individual source JSON embedded. No Blender rigid-body setup or Unreal room assembly performed.

Verified saved/reopened file, exact chair positions and upright orientations, packed images, 27 doorway sample rays clear with adjacent-wall/lintel positive controls, original source SHA unchanged. Overview rendered and visually reviewed. Delivered three-classroom-layouts-blender.zip with prepared blend, overviewPNG, report, verification, source plan/manifest/replayed specs and reusable assembler. Andy need only extract/open prepared blend; no script execution/manual furniture placement. Await one whole-result visual review, then continue approved Unreal room assembly. Use existing Unreal imported reviewed chair mesh/materials. Restore hidden front wall when constructing full room collision. Do not claim aisle overlap proves an exit impassable or a validated evacuation scenario.
