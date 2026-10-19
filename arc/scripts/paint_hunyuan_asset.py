"""Clean a copy of an existing chair and generate/export Hunyuan PBR textures."""

import argparse
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

import trimesh
from huggingface_hub import snapshot_download
from hunyuan_texture_assets import clean_mesh, export_pbr_glb, sample_preview_colors, sha256
from hunyuan_texture_compat import install_torchvision_compat
from hy3dshape.postprocessors import FaceReducer
from render_hunyuan_preview import render_preview


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    source_manifest = json.loads((args.source / "manifest.json").read_text())
    if source_manifest.get("stage") != "completed":
        raise ValueError("Source shape run is not recorded as completed")
    if args.output.resolve() == args.source.resolve():
        raise ValueError("Texture output must be separate from the raw shape run")
    args.output.mkdir(parents=True, exist_ok=False)
    raw_hash = sha256(args.source / "chair.glb")
    shutil.copy2(args.source / "chair.glb", args.output / "chair-raw.glb")
    shutil.copy2(args.source / "manifest.json", args.output / "source-manifest.json")
    shutil.copy2(args.source / "input-foreground.png", args.output / "input-foreground.png")
    cleanup = clean_mesh(args.source / "chair.glb", args.output / "chair-cleaned.glb")
    print(f"Cleaned working copy: {cleanup}", flush=True)
    mesh = trimesh.load(args.output / "chair-cleaned.glb", force="mesh", process=False)
    mesh = FaceReducer()(mesh, max_facenum=80000)
    mesh.export(str(args.output / "chair-paint-input.obj"))
    root = Path("/workspace/hunyuan21")
    manifest = {
        "stage": "cleaned",
        "source_job_id": source_manifest["job_id"],
        "job_id": os.environ.get("SLURM_JOB_ID"),
        "raw_glb_sha256": raw_hash,
        "cleanup": cleanup,
        "paint_input_faces": len(mesh.faces),
        "paint_model": "tencent/Hunyuan3D-2.1",
        "paint_revision": os.environ["HUNYUAN_PAINT_REVISION"],
        "source_revision": os.environ["HUNYUAN_TEXTURE_SOURCE_REVISION"],
        "input_foreground_sha256": sha256(args.source / "input-foreground.png"),
        "dino_revision": os.environ["HUNYUAN_DINO_REVISION"],
        "textures_generated": False,
        "physical_scale_verified": False,
        "collision_mesh_created": False,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    manifest_path = args.output / "manifest.json"

    def save_stage(stage: str) -> None:
        manifest["stage"] = stage
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    save_stage("loading_paint_weights")
    dino = snapshot_download(
        "facebook/dinov2-giant",
        revision=os.environ["HUNYUAN_DINO_REVISION"],
        allow_patterns=["config.json", "preprocessor_config.json", "model.safetensors"],
    )
    install_torchvision_compat()
    from textureGenPipeline import Hunyuan3DPaintConfig, Hunyuan3DPaintPipeline

    conf = Hunyuan3DPaintConfig(max_num_view=6, resolution=512)
    conf.render_size = 1024
    conf.texture_size = 2048  # upstream saves at half size: final maps are 1024 square
    conf.dino_ckpt_path = dino
    conf.realesrgan_ckpt_path = str(root / "texture-weights/RealESRGAN_x4plus.pth")
    pipeline = Hunyuan3DPaintPipeline(conf)
    save_stage("painting")
    pipeline(
        mesh_path=str(args.output / "chair-paint-input.obj"),
        image_path=str(args.output / "input-foreground.png"),
        output_mesh_path=str(args.output / "chair-textured.obj"),
        use_remesh=False,
        save_glb=False,
    )
    manifest["material"] = export_pbr_glb(
        args.output / "chair-textured.obj", args.output / "chair-textured.glb"
    )
    manifest["textures_generated"] = True
    manifest["esrgan_sha256"] = sha256(Path(conf.realesrgan_ckpt_path))
    for name in ("LICENSE", "Notice.txt"):
        shutil.copy2(Path.cwd() / name, args.output / name)
    shutil.copy2(root / "metadata/texture-source-patches.diff", args.output / "source-patches.diff")
    save_stage("textured_glb_exported")
    print("Textured GLB and material maps saved; rendering base-color preview", flush=True)
    mesh = trimesh.load(args.output / "chair-textured.glb", force="mesh", process=False)
    render_preview(
        mesh,
        args.output,
        face_colors=sample_preview_colors(mesh),
        label="AI-generated base color · PBR maps embedded in GLB",
    )
    if sha256(args.source / "chair.glb") != raw_hash:
        raise RuntimeError("Raw source GLB changed during texture processing")
    manifest["raw_source_preserved"] = True
    manifest["completed_at"] = datetime.now(timezone.utc).isoformat()
    save_stage("completed")
    print(f"Finished: {args.output}", flush=True)


if __name__ == "__main__":
    main()
