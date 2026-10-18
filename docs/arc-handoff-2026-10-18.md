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
