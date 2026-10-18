"""Complete this POC chair's collision preview in Blender 5.1.2.
Run once on chair-collision.blend. No files are saved/exported automatically.
The textured render mesh and existing manual colliders are preserved and hidden.
"""
import itertools
import json
import math

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

COLLECTION = 'POC_Complete_Collision_Preview'
RENDER_NAME = 'SM_Chair_Demo'
REPORT_NAME = 'POC_collision_report.json'
# Final (floor-corrected) X/Z gap extents from the prior repair.
GAPS = [(-.181, -.124), (-.085, -.052), (-.017, .022), (.056, .091), (.128, .184)]
LIFT = .02656865119934082


def closed_mesh(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    result = {'vertices': len(bm.verts), 'polygons': len(bm.faces),
              'nonmanifold_edges': sum(not e.is_manifold for e in bm.edges),
              'volume_m3': abs(bm.calc_volume(signed=True))}
    bm.free()
    return result


def make_hull(collection, label, points, index):
    mesh = bpy.data.meshes.new(label + '_hull')
    bm = bmesh.new()
    for point in points:
        bm.verts.new(point)
    bmesh.ops.convex_hull(bm, input=list(bm.verts), use_existing_faces=False)
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    obj = bpy.data.objects.new(f'UCX_{RENDER_NAME}_{index:02d}', mesh)
    collection.objects.link(obj)
    obj['collision_part'] = label
    obj['approximation'] = 'Demo convex proxy, not a measured physical part.'
    obj.display_type = 'WIRE'
    obj.show_in_front = True
    obj.hide_render = True
    obj.color = (.05, .85, 1, 1)
    stats = closed_mesh(mesh)
    if stats['nonmanifold_edges'] or stats['volume_m3'] <= 1e-9:
        raise RuntimeError(f'Invalid hull {label}: {stats}')
    coords = np.array([v.co[:] for v in mesh.vertices])
    for face in mesh.polygons:
        normal = np.array(face.normal[:])
        anchor = np.array(mesh.vertices[face.vertices[0]].co[:])
        if ((coords - anchor) @ normal).max() > 1e-5:
            raise RuntimeError(f'Non-convex hull: {label}, violation={((coords-anchor) @ normal).max()}, normal={normal}, anchor={anchor}')
    obj['validation'] = json.dumps(stats)
    return obj


def box_points(points, angle=0, x_bounds=None):
    """Fit an oriented rectangular envelope. Rotation is about world X."""
    if len(points) < 8:
        raise RuntimeError('Insufficient mesh samples for a collision part.')
    rotation = np.array(Matrix.Rotation(math.radians(angle), 3, 'X'))
    local = points @ rotation
    lo, hi = local.min(axis=0), local.max(axis=0)
    if x_bounds is not None:
        lo[0], hi[0] = x_bounds
    corners = np.array(list(itertools.product(*zip(lo, hi))))
    return corners @ rotation.T


def leg_points(vertices, sign, front):
    """Use clean height bands, avoiding horizontal rungs and apron geometry.
    Flat feet are deliberate demo proxies, all with minimum Z=0.
    """
    part = vertices[(vertices[:, 0] * sign > .17) &
                    ((vertices[:, 1] < -.30) if front else (vertices[:, 1] > .04))]
    samples = []
    for z, low, high in [(0, .005, .025), (.10, .09, .11),
                         (.30, .29, .31), (.35, .34, .36)]:
        section = part[(part[:, 2] >= low) & (part[:, 2] <= high)]
        if len(section) < 8:
            raise RuntimeError('Leg sampling failed; unexpected input mesh.')
        samples.append((z, section[:, :2].min(axis=0), section[:, :2].max(axis=0)))
    # Extend the clean leg section up to just below the seat.
    z0, lo0, hi0 = samples[-2]
    z1, lo1, hi1 = samples[-1]
    t = (.446 - z1) / (z1 - z0)
    samples.pop()  # Used for slope estimation, not a redundant collinear hull ring.
    samples.append((.446, lo1 + t * (lo1 - lo0), hi1 + t * (hi1 - hi0)))
    return [(x, y, z) for z, lo, hi in samples
            for x in (lo[0], hi[0]) for y in (lo[1], hi[1])]


def run():
    if bpy.context.mode != 'OBJECT':
        raise RuntimeError('Return to Object Mode first.')
    if bpy.data.collections.get(COLLECTION) or bpy.data.objects.get(RENDER_NAME):
        raise RuntimeError('Complete preview already exists. Reopen the saved input to restart.')
    source = bpy.data.objects.get('SM_Chair')
    if source is None or source.type != 'MESH':
        raise RuntimeError('Open the saved chair-collision.blend containing SM_Chair.')
    if len(source.data.vertices) != 39992 or len(source.modifiers) != 5:
        raise RuntimeError('This script expects the repaired chair from job 8053348.')
    if any(m.type != 'BOOLEAN' for m in source.modifiers):
        raise RuntimeError('Unexpected modifier stack; no changes made.')
    if max(abs(source.matrix_world[i][j] - (1 if i == j else 0))
           for i in range(4) for j in range(4)) > 1e-5:
        raise RuntimeError('Unexpected chair transform; no changes made.')
    manual = [o for o in bpy.context.scene.objects
              if o.name.startswith(('UBX_SM_Chair_', 'UCX_SM_Chair_'))]
    evaluated = source.evaluated_get(bpy.context.evaluated_depsgraph_get())
    render_mesh = bpy.data.meshes.new_from_object(evaluated, preserve_all_data_layers=True,
                                                depsgraph=bpy.context.evaluated_depsgraph_get())
    vertices = np.array([v.co[:] for v in render_mesh.vertices])
    bounds = np.array([vertices.min(axis=0), vertices.max(axis=0)])
    if (not np.isfinite(vertices).all() or abs(bounds[0, 2]) > 1e-5
            or abs(bounds[1, 2] - 1) > .002):
        bpy.data.meshes.remove(render_mesh)
        raise RuntimeError('Expected floor-corrected one-metre demo chair.')
    render_stats = closed_mesh(render_mesh)
    if render_stats['nonmanifold_edges']:
        bpy.data.meshes.remove(render_mesh)
        raise RuntimeError('Evaluated render mesh is not closed.')
    collection = bpy.data.collections.new(COLLECTION)
    bpy.context.scene.collection.children.link(collection)
    render = bpy.data.objects.new(RENDER_NAME, render_mesh)
    collection.objects.link(render)
    colliders = []
    try:
        def add(label, points):
            collider = make_hull(collection, label, points, len(colliders))
            colliders.append(collider)
            return collider

        def region(xlo, xhi, ylo, yhi, zlo, zhi):
            return vertices[(vertices[:, 0] >= xlo) & (vertices[:, 0] <= xhi) &
                            (vertices[:, 1] >= ylo) & (vertices[:, 1] <= yhi) &
                            (vertices[:, 2] >= zlo) & (vertices[:, 2] <= zhi)]

        # Keep the manually reviewed seat approximation; all proxies use UCX naming.
        add('seat', list(itertools.product((-.27, .27), (-.42, .08), (.4475, .4825))))
        feet = []
        for sign, side in [(-1, 'left'), (1, 'right')]:
            for front in [True, False]:
                feet.append(add(f'{side}_{"front" if front else "rear"}_leg',
                                leg_points(vertices, sign, front)))
        # Outer posts, top/bottom rails and four individual slats. No solid back panel.
        for side, low, high in [('left', -.25, -.181), ('right', .184, .255)]:
            add(side + '_back_post', box_points(region(low, high, 0, .25, .483, 1.001),
                                                angle=-12))
        add('top_back_rail', box_points(region(-.181, .184, 0, .25, .864 + LIFT, 1),
                                        angle=-12, x_bounds=(-.180, .183)))
        add('bottom_back_rail', box_points(region(-.181, .184, 0, .25, .509, .546 + LIFT),
                                           angle=-12, x_bounds=(-.180, .183)))
        slat_intervals = [(GAPS[i][1], GAPS[i + 1][0]) for i in range(4)]
        for i, (low, high) in enumerate(slat_intervals, 1):
            add(f'back_slat_{i}', box_points(region(low, high, 0, .25,
                                                   .546 + LIFT, .864 + LIFT),
                                             angle=-12, x_bounds=(low, high)))
        # Four under-seat aprons and two side stretchers. Centre stays open.
        add('front_apron', box_points(region(-.19, .19, -.405, -.335, .375, .444)))
        add('rear_apron', box_points(region(-.175, .18, .045, .12, .375, .444)))
        for side, low, high in [('left', -.255, -.18), ('right', .18, .263)]:
            add(side + '_apron', box_points(region(low, high, -.335, .045, .375, .444)))
            add(side + '_stretcher', box_points(region(low, high, -.315, .035, .155, .245)))
        # Sample physical openings against collision BVHs, not just visual silhouettes.
        trees = [BVHTree.FromPolygons([v.co[:] for v in c.data.vertices],
                                     [list(p.vertices) for p in c.data.polygons])
                 for c in colliders]
        gap_checks = []
        for low, high in GAPS:
            for z in (.64, .73, .82):
                start = Vector(((low + high) / 2, -1, z))
                if any(t.ray_cast(start, Vector((0, 1, 0)), 2)[0] is not None for t in trees):
                    raise RuntimeError('Collision blocks a repaired backrest opening.')
                gap_checks.append([round((low + high) / 2, 5), z])
        if any(t.ray_cast(Vector((0, -1, .12)), Vector((0, 1, 0)), 2)[0] is not None
               for t in trees):
            raise RuntimeError('Collision blocks the central space under the chair.')
        foot_heights = {f['collision_part']: min(v.co.z for v in f.data.vertices) for f in feet}
        if any(abs(z) > 1e-6 for z in foot_heights.values()):
            raise RuntimeError('Collision feet do not share the Z=0 support plane.')
        render_mesh.calc_loop_triangles()
        report = {
            'blender': bpy.app.version_string, 'source_shape_job': '8052814',
            'source_paint_job': '8053348', 'render_mesh': render.name,
            'render_triangles': len(render_mesh.loop_triangles),
            'render_bounds_m': bounds.tolist(), 'render_topology': render_stats,
            'collider_count': len(colliders),
            'parts': [{'name': c.name, 'part': c['collision_part'],
                       **json.loads(c['validation'])} for c in colliders],
            'backrest_gap_rays_clear': len(gap_checks),
            'under_chair_centre_ray_clear': True, 'foot_min_z_m': foot_heights,
            'assumptions': ['One-metre overall height chosen for demo, not measured.',
                            'Convex proxy fit is approximate; flat collision feet are deliberate.',
                            'No mass, friction, inertia or Chaos stability validation yet.',
                            'Colliders form one future rigid body; no individual joints.',
                            'Source mesh, materials and manual colliders preserved; visibility changed.'],
            'exported': False,
        }
    except Exception:
        for obj in list(collection.objects):
            mesh = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)
        bpy.data.collections.remove(collection)
        raise
    # Commit visibility changes only after all geometry checks pass.
    for obj in [source, *manual]:
        obj.hide_set(True)
        obj.hide_render = True
    render['source_object'] = source.name
    render['demo_height_m'] = 1.0
    render['physical_scale_measured'] = False
    text = bpy.data.texts.get(REPORT_NAME) or bpy.data.texts.new(REPORT_NAME)
    text.clear()
    text.write(json.dumps(report, indent=2))
    bpy.ops.object.select_all(action='DESELECT')
    for collider in colliders:
        collider.select_set(True)
    render.select_set(True)
    bpy.context.view_layer.objects.active = render
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces.active.shading.type = 'MATERIAL'
                area.spaces.active.overlay.show_wireframes = False
                area.spaces.active.region_3d.view_distance = 1.8
                area.spaces.active.region_3d.view_location = (0, -.1, .5)
    print(f'COMPLETE: {len(colliders)} convex colliders; {len(gap_checks)} gap rays clear; four feet at Z=0.')
    print('Inspect the selected wire cages around the textured chair. Original objects remain hidden.')
    print('Save As chair-collision-complete.blend. No export or file save has been performed.')
    return report


if __name__ == '__main__':
    run()
