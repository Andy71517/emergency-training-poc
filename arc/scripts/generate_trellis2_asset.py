"""Generate one inspectable TRELLIS.2 asset from an input photograph."""

import argparse
import hashlib
import json
import os
from pathlib import Path

os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

import cv2
import imageio
import o_voxel
import torch
from PIL import Image
from trellis2.pipelines import Trellis2ImageTo3DPipeline
from trellis2.renderers import EnvMap
from trellis2.utils import render_utils


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if not args.image.is_file():
        parser.error(f"Input image does not exist: {args.image}")
    args.output.mkdir(parents=True, exist_ok=True)

    model_id = "microsoft/TRELLIS.2-4B"
    print(f"Loading {model_id}", flush=True)
    pipeline = Trellis2ImageTo3DPipeline.from_pretrained(model_id)
    pipeline.cuda()
    print("Generating 512-resolution mesh", flush=True)
    with Image.open(args.image) as source:
        mesh = pipeline.run(source.convert("RGB"), seed=args.seed, pipeline_type="512")[0]
    mesh.simplify(16777216)  # nvdiffrast index limit

    hdri = cv2.imread("assets/hdri/forest.exr", cv2.IMREAD_UNCHANGED)
    if hdri is None:
        raise FileNotFoundError("TRELLIS environment map assets/hdri/forest.exr")
    envmap = EnvMap(torch.tensor(cv2.cvtColor(hdri, cv2.COLOR_BGR2RGB), dtype=torch.float32, device="cuda"))
    frames = render_utils.make_pbr_vis_frames(render_utils.render_video(mesh, envmap=envmap))
    imageio.imwrite(args.output / "preview.png", frames[0])
    imageio.mimsave(args.output / "turntable.mp4", frames, fps=15)
    print("Saved preview.png and turntable.mp4", flush=True)

    glb = o_voxel.postprocess.to_glb(
        vertices=mesh.vertices,
        faces=mesh.faces,
        attr_volume=mesh.attrs,
        coords=mesh.coords,
        attr_layout=mesh.layout,
        voxel_size=mesh.voxel_size,
        aabb=[[-0.5, -0.5, -0.5], [0.5, 0.5, 0.5]],
        decimation_target=100000,
        texture_size=1024,
        remesh=True,
        remesh_band=1,
        remesh_project=0,
        verbose=True,
    )
    glb.export(args.output / "chair.glb", extension_webp=False)
    manifest = {
        "model": model_id,
        "source_revision": os.environ.get("TRELLIS_SOURCE_REVISION"),
        "input_sha256": hashlib.sha256(args.image.read_bytes()).hexdigest(),
        "seed": args.seed,
        "resolution": 512,
        "gpu": torch.cuda.get_device_name(0),
        "files": {p.name: p.stat().st_size for p in args.output.iterdir() if p.is_file()},
    }
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Finished: {args.output}", flush=True)


if __name__ == "__main__":
    main()
