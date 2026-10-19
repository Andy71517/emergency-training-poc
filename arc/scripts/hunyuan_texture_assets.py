"""Mesh cleanup and explicit glTF PBR export, independent of GPU inference."""

import hashlib
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean_mesh(source: Path, output: Path) -> dict:
    mesh = trimesh.load(source, force="mesh", process=False)
    if not np.isfinite(mesh.vertices).all() or len(mesh.faces) == 0:
        raise ValueError("Source mesh is empty or has non-finite coordinates")
    original_faces = len(mesh.faces)
    original_bounds = mesh.bounds.copy()
    mesh.update_faces(mesh.nondegenerate_faces())
    mesh.update_faces(mesh.unique_faces())
    mesh.remove_unreferenced_vertices()
    if not mesh.is_watertight or not mesh.is_winding_consistent:
        raise ValueError("Minimal cleanup did not produce a closed, consistently wound mesh")
    if not np.allclose(mesh.bounds, original_bounds):
        raise ValueError("Minimal cleanup unexpectedly changed the mesh bounds")
    mesh.export(str(output))
    return {
        "original_faces": original_faces,
        "cleaned_faces": len(mesh.faces),
        "removed_faces": original_faces - len(mesh.faces),
        "vertices": len(mesh.vertices),
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "bounds": mesh.bounds.tolist(),
        "physical_scale_verified": False,
    }


def export_pbr_glb(obj: Path, output: Path) -> dict:
    mesh = trimesh.load(obj, force="mesh", process=False)
    uv = getattr(mesh.visual, "uv", None)
    if uv is None or not np.isfinite(uv).all():
        raise ValueError("Painted mesh has no valid UV coordinates")
    with Image.open(obj.with_suffix(".jpg")) as image:
        albedo = image.convert("RGB")
    with Image.open(obj.with_name(obj.stem + "_roughness.jpg")) as image:
        roughness = image.convert("L")
    with Image.open(obj.with_name(obj.stem + "_metallic.jpg")) as image:
        metallic = image.convert("L")
    if roughness.size != metallic.size:
        raise ValueError("Roughness and metallic maps have different dimensions")
    # glTF metallic/roughness convention: roughness in G, metallic in B.
    packed = Image.merge("RGB", (Image.new("L", roughness.size, 255), roughness, metallic))
    packed.save(output.with_name("metallic-roughness.png"))
    mesh.visual = trimesh.visual.TextureVisuals(
        uv=uv,
        material=trimesh.visual.material.PBRMaterial(
            name="Hunyuan generated chair PBR",
            baseColorTexture=albedo,
            metallicRoughnessTexture=packed,
            metallicFactor=1.0,
            roughnessFactor=1.0,
        ),
    )
    mesh.export(str(output), include_normals=True)
    loaded = trimesh.load(output, force="mesh", process=False)
    material = loaded.visual.material
    if material.baseColorTexture is None or material.metallicRoughnessTexture is None:
        raise ValueError("GLB export lost generated material maps")
    return {
        "faces": len(loaded.faces),
        "vertices": len(loaded.vertices),
        "albedo_size": list(albedo.size),
        "uv_vertices": len(loaded.visual.uv),
        "base_color_embedded": True,
        "metallic_roughness_embedded": True,
    }


def sample_preview_colors(mesh: trimesh.Trimesh) -> np.ndarray:
    image = np.asarray(mesh.visual.material.baseColorTexture.convert("RGB"))
    uv = np.clip(mesh.visual.uv[mesh.faces].mean(axis=1), 0, 1)
    x = np.rint(uv[:, 0] * (image.shape[1] - 1)).astype(int)
    y = np.rint((1 - uv[:, 1]) * (image.shape[0] - 1)).astype(int)
    return image[y, x].astype(float) / 255.0
