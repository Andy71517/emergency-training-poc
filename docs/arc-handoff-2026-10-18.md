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
