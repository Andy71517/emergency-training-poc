> **Historical checkpoint/plan:** retained as written for its date. For current implementation, evidence and setup, use [current status](current-status.md) and the [documentation index](README.md). Old branch, approval and next-action instructions below may be superseded.

> Historical checkpoint. For the current working state and next actions, start with [arc-handoff-2026-10-19.md](arc-handoff-2026-10-19.md). Later sections below preserve the earlier troubleshooting history.

# ARC visual POC handoff — 2026-09-28

Use this file to resume the ARC image-to-3D POC. It records what actually ran, what remains blocked, and the next decision. No model-generated chair mesh exists yet.

## Goal and scope

The near-term goal is a visually inspectable demo for Dr. Cameron: create a chair asset with ARC compute, inspect a turntable and GLB, clean the asset in Blender, then import it into Unreal Engine for a scenario with Chaos Physics. The browser Rapier preview and deterministic backend are separate work and do not substitute for this pipeline. Andy is using ARC Open OnDemand and wants beginner-friendly, one-step-at-a-time terminal guidance. Changes are approved batch by batch.

## GitHub work

- Batch 1 visual physics demo: draft PR #1, `codex/visual-physics-batch-1`, commit `aa214b2`. It is a browser preview and is not merged.
- Batch 2 ARC TRELLIS runtime and first chair attempt: draft PR #2, `codex/arc-trellis-runtime-fix`. The ARC checkout tracks this branch; it is not merged. The branch started from `main` commit `47ce108`.
- PR #2 first fixed missing FlashAttention prerequisites (`psutil`, `packaging`) in commit `170f280`, then kept pip temporary files and cache on the same filesystem in `2c17d2f`. Three files were added for inference (`arc/scripts/generate_trellis2_asset.py`, `arc/jobs/generate_trellis2_chair.sbatch`, and `arc/scripts/submit_trellis2_chair.sh`), and commit `d9324a0` fixed the script's TRELLIS import path. Fetch the current PR branch before continuing; do not assume this list is a complete commit history.
- The reference image is `assets/generated/wooden-chair-reference.png` in the local ChatGPT scratch workspace and was uploaded to ARC as `$ARC_PROJECT_WORKSPACE/trellis2/inputs/wooden-chair.png`. The local path is a generated artifact, not tracked in Git. The ARC copy is 1.6 MB.

## ARC setup and results

- ARC host: `tinkercliffs2`. Checkout: `/home/anirudhalledula/emergency-training-poc`. Private settings in ignored `arc/.env`; never paste the whole file or tokens into chat or commit them.
- Project workspace: `/projects/research-mel/anirudhalledula/emergency-training-poc`. The correct Slurm combination observed from prior jobs is account `research-mel`, partition `a100_normal_q`, QoS `tc_a100_normal_base`. On 2026-09-28, `arc/.env` had `research_mel` with an underscore and was corrected locally to `research-mel` after an invalid account/partition submission.
- TRELLIS.2 source checkout at `75fbf0183001ed9876c8dbb35de6b68552ee08bd`, Conda runtime and Apptainer SIF live in project storage. Build job `7759899` failed on a FlashAttention wheel `Invalid cross-device link`; job `7759934` completed in 9m51s with exit code `0:0` after the pip temp/cache fix. Earlier job `7352823` had failed because `psutil` was missing at FlashAttention metadata generation.
- Runtime check job `7760234` completed in 17s with exit code `0:0`. It printed PyTorch `2.6.0+cu124`, `torch.cuda.is_available() == True`, NVIDIA A100-SXM4-80GB (81920 MiB), and successful imports for `trellis2` and `o_voxel`.
- The chair image is at `$ARC_PROJECT_WORKSPACE/trellis2/inputs/wooden-chair.png`. Inference job `7760508` failed in 34s with `ModuleNotFoundError: trellis2`; commit `d9324a0` fixed `PYTHONPATH`. Job `7760687` then reached `Loading microsoft/TRELLIS.2-4B` but failed in 3m30s with a Hugging Face `401 GatedRepoError` for `facebook/dinov3-vitl16-pretrain-lvd1689m/config.json`. This is TRELLIS.2's separate DINOv3 image encoder dependency. No `preview.png`, `turntable.mp4`, or `chair.glb` has been confirmed. See `arc/results/trellis2-chair-7760687.{out,err}` on ARC.

## Current blocker and decision

Andy submitted the access request on the Hugging Face page for `facebook/dinov3-vitl16-pretrain-lvd1689m` on 2026-09-28. Status: **request pending, awaiting repository-author review**. Do not submit the TRELLIS job again until the same Hugging Face account has been granted access and authenticated privately on ARC. Never ask Andy to paste an HF token into chat, `arc/.env`, or Git. The job sets `HF_HOME=/workspace/cache/huggingface`; a future CLI login must persist credentials in the matching bind-mounted location, and the gate should be checked without occupying an A100 first.

To avoid waiting for DINOv3 before a visual demo, Hunyuan3D 2.1 was researched as an alternative image-to-3D source. Its official repository documents image-to-shape, texture generation, GLB output, and approximately 29 GB VRAM for shape plus texture; the ARC A100 has 80 GB. Its Hugging Face model listing appears publicly accessible, but its distinct Tencent community license and actual ARC dependencies must be reviewed before use. **No Hunyuan runtime or job has been implemented or submitted.** A Hunyuan fallback batch was proposed, but Andy has not approved it. Pause here and do not start that batch until he chooses it. Keep TRELLIS as the intended path and label any Hunyuan output accurately.

## Resume checklist

1. Ask whether DINOv3 access has been granted and whether Andy wants to approve the separate Hunyuan fallback batch. The existing approved TRELLIS route can continue as soon as access is granted.
2. For TRELLIS after access: guide private Hugging Face CLI authentication into the same `HF_HOME` visible inside the Apptainer job; verify gated model access on a login node with only a lightweight metadata request; then rerun `bash arc/scripts/submit_trellis2_chair.sh`. Watch `squeue -j JOB_ID`, `sacct -j JOB_ID -X --format=JobID,State,ExitCode,Elapsed`, and `arc/results/trellis2-chair-JOB_ID.{out,err}`.
3. For Hunyuan if approved: first review its model license and exact published setup, then create a separate ARC environment/job that consumes the already uploaded chair reference. Keep its generated outputs and provenance separate from TRELLIS.
4. When either model produces a chair: inspect the actual `preview.png`/turntable and `chair.glb` visually; validate geometry and scale; only then prepare Blender cleanup, collision geometry, and Unreal import/Chaos scenario. Do not claim that stage is done until the files have been inspected.

Useful official references: [TRELLIS.2 repository](https://github.com/microsoft/TRELLIS.2), [TRELLIS.2 model](https://huggingface.co/microsoft/TRELLIS.2-4B), [gated DINOv3 dependency](https://huggingface.co/facebook/dinov3-vitl16-pretrain-lvd1689m), [Hunyuan3D 2.1 repository](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1), [Hunyuan3D 2.1 model](https://huggingface.co/tencent/Hunyuan3D-2.1).
