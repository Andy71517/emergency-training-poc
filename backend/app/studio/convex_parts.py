"""CPU decomposition in an isolated process; never changes the render mesh."""
import argparse
import json
from pathlib import Path

import coacd
import numpy as np
from scipy.spatial import ConvexHull


def decompose(source, output):
    with np.load(source, allow_pickle=False) as data:
        vertices, faces = data['vertices'], data['faces']
    if vertices.ndim != 2 or vertices.shape[1] != 3 or not 4 <= len(vertices) <= 1_000_000 or not np.isfinite(vertices).all():
        raise ValueError('Invalid collision input vertices.')
    if faces.ndim != 2 or faces.shape[1] != 3 or not 4 <= len(faces) <= 1_000_000 or not np.issubdtype(faces.dtype, np.integer) or faces.min() < 0 or faces.max() >= len(vertices):
        raise ValueError('Invalid collision input triangles.')
    coacd.set_log_level('warn')
    parts = coacd.run_coacd(coacd.Mesh(vertices.astype(np.float64), faces.astype(np.int32)),
                            threshold=.02, real_metric=True, max_convex_hull=32,
                            max_ch_vertex=64, decimate=True, resolution=2000, mcts_iterations=100,
                            preprocess_resolution=50, seed=42)
    if not 1 <= len(parts) <= 32:
        raise ValueError('Collision decomposition exceeded the bounded hull budget.')
    hulls = []
    for points, _ in parts:
        points = np.unique(np.asarray(points, dtype=float), axis=0)
        if not 4 <= len(points) <= 64 or not np.isfinite(points).all():
            raise ValueError('Invalid convex piece.')
        hull = ConvexHull(points)
        if hull.volume <= 1e-10:
            raise ValueError('Degenerate collision piece.')
        triangles = hull.simplices.copy()
        for triangle, equation in zip(triangles, hull.equations):
            a, b, c = points[triangle]
            if np.dot(np.cross(b-a, c-a), equation[:3]) < 0:
                triangle[1], triangle[2] = triangle[2], triangle[1]
        if (points.min(axis=0) < vertices.min(axis=0)-.05).any() or (points.max(axis=0) > vertices.max(axis=0)+.05).any():
            raise ValueError('Collision piece extends too far outside the input bounds.')
        hulls.append({'vertices': points.tolist(), 'faces': triangles.tolist(), 'volume_m3': float(hull.volume)})
    report = {'method': 'CoACD', 'version': '1.0.14', 'threshold_m': .02,
              'max_hulls': 32, 'max_vertices_per_hull': 64, 'seed': 42, 'hulls': hulls,
              'fit_review_required': True, 'physics_calibrated': False}
    Path(output).write_text(json.dumps(report, allow_nan=False), encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    decompose(args.source, args.output)
