"""Stage a generated furniture GLB for visual review. No collision or physics claims."""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


def bounds(objects):
    points = [o.matrix_world @ Vector(v) for o in objects for v in o.bound_box]
    low = Vector(tuple(min(v[i] for v in points) for i in range(3)))
    high = Vector(tuple(max(v[i] for v in points) for i in range(3)))
    return low, high


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    request = json.loads(args.request.read_text(encoding='utf-8'))
    args.output.mkdir(parents=True, exist_ok=False)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(args.source))
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    if not meshes:
        raise ValueError('The GLB contains no mesh geometry.')
    for obj in meshes:
        matrix = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = matrix
    for obj in list(bpy.context.scene.objects):
        if obj.type != 'MESH':
            bpy.data.objects.remove(obj, do_unlink=True)
    bpy.context.view_layer.update()
    low, high = bounds(meshes)
    dimensions = high-low
    if not all(math.isfinite(n) and n > 0.00001 for n in dimensions):
        raise ValueError('Invalid model bounds.')
    target = request['dimensions_m']
    scale = target[2]/dimensions.z
    translation = Vector((-(low.x+high.x)*.5*scale, -(low.y+high.y)*.5*scale, -low.z*scale))
    transform = Matrix.Translation(translation) @ Matrix.Scale(scale, 4)
    for obj in meshes:
        obj.matrix_world = transform @ obj.matrix_world
    bpy.context.view_layer.update()
    low, high = bounds(meshes)
    actual = list(high-low)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1
    # Single-user copy: source GLB is read only; all textures are packed into the review file.
    bpy.ops.file.pack_all()
    vertices = sum(len(o.data.vertices) for o in meshes)
    faces = sum(len(o.data.polygons) for o in meshes)
    report = {'asset_id': request['asset_id'], 'stage': 'visual_review_required',
        'target_dimensions_m': target, 'staged_dimensions_m': actual,
        'scale_method': 'Uniform height match; width and depth are preserved, not distorted to fit.',
        'target_size_matches_within_15_percent': all(abs(a-b)/b <= .15 for a,b in zip(actual,target)),
        'floor_at_z_zero': True, 'geometry_centered_xy': True, 'pivot_review_required': True, 'vertices': vertices, 'faces': faces,
        'orientation_review_required': True, 'physical_scale_verified': False,
        'collision_mesh_created': False, 'room_compatible': False, 'simulation_validated': False}
    (args.output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output/'furniture-review.blend'))
    print('Furniture review copy saved. Confirm orientation, dimensions, geometry and materials before collision preparation.')


if __name__ == '__main__':
    main()
