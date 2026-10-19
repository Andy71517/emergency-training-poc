"""Generate a Hunyuan3D 2.1 chair mesh, then render its actual geometry."""

import argparse
import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

import torch
from huggingface_hub import snapshot_download
from hy3dshape.pipelines import Hunyuan3DDiTFlowMatchingPipeline
from hy3dshape.postprocessors import FaceReducer
from hy3dshape.rembg import BackgroundRemover
from PIL import Image
from render_hunyuan_preview import render_preview

MODEL_ID = "tencent/Hunyuan3D-2.1"
MODEL_REVISION = "07d6dc9694e0ea942683bf6e3e374887d9f5b054"
MODEL_SUBFOLDER = "hunyuan3d-dit-v2-1"
CHECKPOINT_SHA256 = "6b519fc7242f78e9b5f47ea4d55668fe3d944a2d27332f4ca68d29a6ff603f5e"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if not args.image.is_file():
        parser.error(f"Missing input: {args.image}")
    args.output.mkdir(parents=True, exist_ok=True)
    manifest_path = args.output / "manifest.json"
    manifest = {
        "model": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "source_revision": os.environ.get("HUNYUAN_SOURCE_REVISION"),
        "job_id": os.environ.get("SLURM_JOB_ID"),
        "seed": args.seed,
        "input_sha256": sha256(args.image),
        "textures_generated": False,
        "physical_scale_verified": False,
        "collision_mesh_created": False,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "stage": "loading",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    source_root = Path(os.environ["PYTHONPATH"].split(os.pathsep)[0]).parent
    for name in ("LICENSE", "Notice.txt"):
        shutil.copy2(source_root / name, args.output / name)
    print("Downloading/loading pinned Hunyuan shape checkpoint (about 7.4 GB)", flush=True)
    model_dir = Path(
        snapshot_download(
            MODEL_ID,
            revision=MODEL_REVISION,
            allow_patterns=[f"{MODEL_SUBFOLDER}/config.yaml", f"{MODEL_SUBFOLDER}/model.fp16.ckpt"],
        )
    )
    checkpoint = model_dir / MODEL_SUBFOLDER / "model.fp16.ckpt"
    if sha256(checkpoint) != CHECKPOINT_SHA256:
        raise ValueError("Checkpoint SHA256 does not match the published revision")
    pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_single_file(
        str(checkpoint),
        str(model_dir / MODEL_SUBFOLDER / "config.yaml"),
        device="cuda",
        dtype=torch.float16,
        use_safetensors=False,
    )
    with Image.open(args.image) as source:
        image = source.convert("RGBA")
    print("Removing background", flush=True)
    image = BackgroundRemover()(image)
    if image.getchannel("A").getextrema()[1] == 0:
        raise ValueError("Background removal produced an empty foreground")
    image.save(args.output / "input-foreground.png")
    print("Generating chair shape", flush=True)
    mesh = pipeline(
        image=image,
        num_inference_steps=30,
        octree_resolution=256,
        mc_algo="mc",
        generator=torch.Generator(device="cuda").manual_seed(args.seed),
    )[0]
    if mesh is None or len(mesh.faces) == 0:
        raise ValueError("Model returned an empty mesh")
    # Keep the generated geometry before preview reduction for Blender review.
    mesh.export(str(args.output / "chair.glb"))
    mesh.export(str(args.output / "chair.ply"))
    manifest.update(
        stage="shape_exported",
        vertices=len(mesh.vertices),
        faces=len(mesh.faces),
        gpu=torch.cuda.get_device_name(0),
        checkpoint_sha256=CHECKPOINT_SHA256,
    )
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print("Saved chair.glb and chair.ply; rendering geometry preview", flush=True)
    preview_mesh = FaceReducer()(mesh.copy(), max_facenum=12000)
    render_preview(preview_mesh, args.output)
    manifest.update(stage="completed", completed_at=datetime.now(timezone.utc).isoformat())
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Finished: {args.output}", flush=True)


if __name__ == "__main__":
    main()
