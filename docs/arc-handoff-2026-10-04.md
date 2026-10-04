# ARC visual POC handoff — 2026-10-04

Read together with `docs/arc-handoff-2026-09-28.md` for previous job IDs and runtime results.

Andy reports DINOv3 access is still pending. He authorized pivoting to Hunyuan while preserving TRELLIS. The new lane is in branch `codex/arc-hunyuan-chair`, based on the existing Batch 2 branch. Neither prior draft PR was merged at this session's start.

The Hunyuan lane reuses the existing container and uploaded wooden-chair reference, but builds its own Python environment under `$ARC_PROJECT_WORKSPACE/hunyuan21`. Source commit: `82920d643c0dc2f7bfd7255f45f62d386edfe60c`. Shape weights: `tencent/Hunyuan3D-2.1`, revision `07d6dc9694e0ea942683bf6e3e374887d9f5b054`, SHA256 `6b519fc7242f78e9b5f47ea4d55668fe3d944a2d27332f4ca68d29a6ff603f5e`. The published config embeds DINOv2 and does not load the gated DINOv3 model.

The prepared batch includes a lightweight access check before GPU submission, build-time imports/CUDA verification, a geometry-only inference job, GLB/PLY export, a headless shaded preview/MP4 renderer, and output provenance. It excludes texture generation from the first run so the first gate is visible chair geometry. No Hunyuan job has yet run on ARC; local validation cannot establish GPU/model success.

Resume with `docs/arc-hunyuan-runbook.md`. First confirm the ARC checkout has no uncommitted tracked changes, fetch/switch to `codex/arc-hunyuan-chair`, confirm the existing image and model access, then submit `bash arc/scripts/submit_hunyuan.sh build`. Only after its import/CUDA check passes submit `bash arc/scripts/submit_hunyuan.sh chair`. Review actual output before texture, Blender, or Unreal/Chaos work. The TRELLIS gate remains pending and its jobs should stay paused until access is granted and private Hugging Face authentication is verified.
