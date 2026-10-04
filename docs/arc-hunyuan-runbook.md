# ARC Hunyuan chair: geometry first

This lane uses Hunyuan3D 2.1 to generate one chair from the reference already on ARC. It has its own environment, cache, output directories, and provenance. TRELLIS.2 remains available after DINOv3 access is granted. The first Hunyuan job generates geometry only; its preview uses a plain shaded material. PBR texture generation is the next milestone after we inspect the mesh.

## Before submitting

In an Open OnDemand terminal, from the repository root, fetch and switch to `codex/arc-hunyuan-chair`. Preserve local changes if `git status` shows any. The ignored `arc/.env` is reused. Confirm `ARC_ACCOUNT=research-mel`, `ARC_GPU_PARTITION=a100_normal_q`, and `ARC_GPU_QOS=tc_a100_normal_base` privately; do not paste the whole file.

```bash
source arc/scripts/load_arc_config.sh
ls -lh "$ARC_PROJECT_WORKSPACE/trellis2/inputs/wooden-chair.png"
bash arc/scripts/check_hunyuan_access.sh
```

The HTTP check fetches only a small config and sends a HEAD request for the checkpoint. It allocates no GPU and downloads no checkpoint. If it fails, inspect the response before submitting. The source and model revisions are pinned in `arc/scripts/hunyuan_config.sh`. We use the official 7.37 GB shape checkpoint and verify its published SHA256. Background removal separately downloads the default rembg/U2Net model on first inference.

## Build and verify

```bash
bash arc/scripts/submit_hunyuan.sh build
```

This builds Python 3.10/PyTorch 2.5.1 with CUDA 12.4 in `$ARC_PROJECT_WORKSPACE/hunyuan21/environment`, using the existing CUDA container. It installs only the shape inference and preview dependencies, then checks imports and GPU access. It does not alter the TRELLIS environment or download Hunyuan model weights. Its limit is one hour, eight CPUs, 64 GB RAM, and one GPU; finish time depends on the queue and package downloads.

Replace `JOB_ID` with the printed number:

```bash
squeue -j JOB_ID
sacct -j JOB_ID -X --format=JobID,State,ExitCode,Elapsed
tail -n 60 arc/results/hunyuan-build-JOB_ID.out
tail -n 80 arc/results/hunyuan-build-JOB_ID.err
```

Continue only after `COMPLETED`, `0:0`, and the log reports `Hunyuan shape imports and CUDA: OK`. Successful builds save a ready marker and package freeze under `hunyuan21/metadata`.

## Generate the first mesh

```bash
bash arc/scripts/submit_hunyuan.sh chair
```

The job copies the existing reference into `hunyuan21/inputs`, downloads the pinned shape checkpoint, removes the image background, and runs 30 inference steps with seed 42 and a 256-resolution mesh extraction. Logs use `arc/results/hunyuan-chair-JOB_ID.{out,err}`. Outputs go to `$ARC_PROJECT_WORKSPACE/hunyuan21/outputs/wooden-chair-JOB_ID/`:

- `input-foreground.png`: inspect background removal before judging the mesh.
- `chair.glb` and `chair.ply`: original generated geometry for Blender inspection, with no generated wood texture.
- `preview.png` and `turntable.mp4`: a shaded view of that generated geometry. A reduced copy is used for rendering; the GLB retains the original mesh.
- `manifest.json`: model/source revision, checkpoint and reference hashes, seed, counts, stage, and explicit texture/scale/collision status.
- `LICENSE` and `Notice.txt`: upstream notices accompanying this lane's result.

If rendering fails after `chair.glb` is written, preserve it and regenerate the preview with `render_hunyuan_preview.py` in the Hunyuan environment. Do not repeat model inference just to make a preview.

Use Open OnDemand Files to download the preview/turntable and GLB from the output folder. Inspect the actual result before declaring the lane successful. The first gate is a recognisable chair, usable legs/backrest, and an inspectable GLB. Its physical scale, collision geometry, mass, friction, and Unreal behavior have not been validated.

## Next milestones

After the geometry passes visual review, add Hunyuan's texture runtime and generate PBR materials in a subsequent batch. Then do Blender scale/orientation/topology cleanup and create simple collision geometry. Finally import into Unreal and demonstrate Chaos gravity, collision, tipping, and a simple scenario. Keep the existing browser demo and deterministic backend connected to this plan without treating them as proof of ARC generation.

The model has a Tencent community license, not an unrestricted global license. The current license excludes the EU, UK, and South Korea, restricts some downstream uses, and requires disclosure for public AI-generated content. This work is a US-based research demo; recheck terms before wider deployment or distribution. See [official license](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1/blob/main/LICENSE), [setup](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1), and [model files](https://huggingface.co/tencent/Hunyuan3D-2.1/tree/main/hunyuan3d-dit-v2-1).
