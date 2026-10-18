"""Render a geometry-only turntable without a display server or OpenGL."""

import argparse
from pathlib import Path

import imageio.v2 as imageio
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def render_preview(
    mesh: trimesh.Trimesh,
    output: Path,
    *,
    face_colors: np.ndarray | None = None,
    label: str = "AI-generated chair geometry · no generated texture",
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    # glTF uses Y up; rotate into matplotlib's Z-up view without changing the asset.
    rotation = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]])
    vertices = mesh.vertices @ rotation.T
    normals = mesh.face_normals @ rotation.T
    low, high = vertices.min(axis=0), vertices.max(axis=0)
    center = (low + high) / 2
    radius = max(high - low) * 0.6
    if radius <= 0 or not np.isfinite(vertices).all():
        raise ValueError("Cannot render degenerate or non-finite mesh")
    light = np.array([0.4, -0.6, 0.7])
    light /= np.linalg.norm(light)
    intensity = 0.35 + 0.65 * np.clip(normals @ light, 0, 1)
    if face_colors is None:
        face_colors = np.tile([0.65, 0.73, 0.8], (len(mesh.faces), 1))
    if face_colors.shape != (len(mesh.faces), 3) or not np.isfinite(face_colors).all():
        raise ValueError("Preview colors must be finite RGB values for every face")
    colors = intensity[:, None] * np.clip(face_colors, 0, 1)
    fig = plt.figure(figsize=(5.12, 5.12), dpi=100, facecolor="#f1f3f5")
    ax = fig.add_subplot(111, projection="3d", computed_zorder=False)
    ax.add_collection3d(Poly3DCollection(vertices[mesh.faces], facecolors=colors, linewidths=0))
    ax.set(
        xlim=(center[0] - radius, center[0] + radius),
        ylim=(center[1] - radius, center[1] + radius),
        zlim=(center[2] - radius, center[2] + radius),
    )
    ax.set_box_aspect((1, 1, 1))
    ax.set_axis_off()
    fig.text(0.5, 0.04, label, ha="center", size=9)
    fig.subplots_adjust(left=0, right=1, bottom=0.08, top=1)
    try:
        with imageio.get_writer(output / "turntable.mp4", fps=12, codec="libx264") as writer:
            for index, azimuth in enumerate(np.linspace(30, 390, 48, endpoint=False)):
                ax.view_init(elev=20, azim=azimuth)
                fig.canvas.draw()
                frame = np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy()
                if index == 0:
                    imageio.imwrite(output / "preview.png", frame)
                writer.append_data(frame)
    finally:
        plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mesh", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    render_preview(trimesh.load(args.mesh, force="mesh"), args.output)
