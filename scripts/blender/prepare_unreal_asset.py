"""Trusted Blender worker: minimal cleanup, preserve source, import UCX and export.

Called only by the project MCP server. Collision decomposition is a separate CPU
process; the render mesh is never replaced by a collision hull or invented repair.
"""
import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def bounds(obj):
    points = np.array([tuple(obj.matrix_world @ Vector(p)) for p in obj.bound_box])
    return points.min(axis=0), points.max(axis=0)


def mesh_stats(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    stats = {'vertices': len(bm.verts), 'faces': len(bm.faces),
             'boundary_edges': sum(e.is_boundary for e in bm.edges),
             'nonmanifold_edges': sum(not e.is_manifold for e in bm.edges),
             'volume_m3': abs(bm.calc_volume(signed=True))}
    bm.free()
    return stats


def cleanup(args):
    request = json.loads(args.request.read_bytes())
    if (args.output/'cleaned.blend').exists():
        raise ValueError('A cleanup result already exists; use a new preparation run.')
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(args.source))
    originals = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    if not originals or sum(len(o.data.polygons) for o in originals) > 1_000_000:
        raise ValueError('Expected bounded furniture mesh geometry.')
    source_collection = bpy.data.collections.new('Preserved source · never export')
    bpy.context.scene.collection.children.link(source_collection)
    export_collection = bpy.data.collections.new('Unreal export candidate')
    bpy.context.scene.collection.children.link(export_collection)
    copies = []
    for original in originals:
        original.select_set(False)
        obj = bpy.data.objects.new('Working copy', original.data.copy())
        obj.matrix_world = original.matrix_world.copy()
        export_collection.objects.link(obj)
        copies.append(obj)
        for collection in list(original.users_collection):
            collection.objects.unlink(original)
        source_collection.objects.link(original)
    source_collection.hide_viewport = True
    source_collection.hide_render = True
    for obj in list(bpy.context.scene.objects):
        if obj.type != 'MESH':
            bpy.data.objects.remove(obj, do_unlink=True)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in copies:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = copies[0]
    bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = 'SM_Asset'
    obj.data.transform(obj.matrix_world)
    obj.matrix_world = Matrix.Identity(4)
    before = mesh_stats(obj.data)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    if any(not all(math.isfinite(n) for n in v.co) for v in bm.verts):
        raise ValueError('Non-finite geometry.')
    # Only collapsed geometry and coincident vertices; do not fill holes or cut new openings.
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-7)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-8, edges=list(bm.edges))
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.transform(Matrix.Rotation(math.radians(args.yaw), 4, 'Z'))
    obj.data.update()
    bpy.context.view_layer.update()
    low, high = bounds(obj)
    dimensions = high-low
    if not np.isfinite(dimensions).all() or (dimensions < 1e-5).any():
        raise ValueError('Empty or flat generated geometry.')
    factor = request['dimensions_m'][2]/dimensions[2]
    translation = Vector((-float((low[0]+high[0])*.5*factor),
                          -float((low[1]+high[1])*.5*factor), -float(low[2]*factor)))
    obj.data.transform(Matrix.Translation(translation) @ Matrix.Scale(float(factor), 4))
    obj.data.update()
    bpy.context.view_layer.update()
    low, high = bounds(obj)
    actual = (high-low).tolist()
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1
    obj.data.calc_loop_triangles()
    vertices = np.array([v.co[:] for v in obj.data.vertices], dtype=np.float64)
    faces = np.array([t.vertices[:] for t in obj.data.loop_triangles], dtype=np.int32)
    np.savez(args.output/'collision-input.npz', vertices=vertices, faces=faces)
    bpy.ops.file.pack_all()
    target = request['dimensions_m']
    report = {'asset_id': request['asset_id'], 'source_sha256': sha(args.source),
              'stage': 'cleaned', 'source_preserved': True, 'before_cleanup': before,
              'after_cleanup': mesh_stats(obj.data), 'staged_dimensions_m': actual,
              'target_dimensions_m': target, 'yaw_degrees': args.yaw,
              'target_size_matches_within_15_percent': all(abs(a-b)/b <= .15 for a, b in zip(actual, target)),
              'scale_method': 'Uniform height match; generated proportions preserved.',
              'floor_at_z_zero': abs(float(low[2])) < 1e-5,
              'collision_mesh_created': False, 'room_compatible': False,
              'physical_scale_verified': False, 'simulation_validated': False}
    save_json(args.output/'report.json', report)
    extract_materials(args.source, obj, args.output)
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output/'cleaned.blend'))


def extract_materials(source, obj, folder):
    raw = source.read_bytes()
    size = struct.unpack('<I', raw[12:16])[0]
    document = json.loads(raw[20:20+size])
    offset = 20+size
    binary_size, kind = struct.unpack('<II', raw[offset:offset+8])
    if kind != 0x004e4942:
        raise ValueError('Expected embedded geometry and texture data.')
    binary = raw[offset+8:offset+8+binary_size]
    textures = folder/'textures'
    textures.mkdir()
    images = {}
    for index, image in enumerate(document.get('images', [])):
        if 'bufferView' not in image or image.get('mimeType') not in ('image/png', 'image/jpeg'):
            raise ValueError('Expected embedded PNG/JPEG textures for the Unreal package.')
        view = document['bufferViews'][image['bufferView']]
        start = view.get('byteOffset', 0)
        extension = 'png' if image['mimeType'] == 'image/png' else 'jpg'
        relative = f'textures/image-{index}.{extension}'
        data = binary[start:start+view['byteLength']]
        if len(data) != view['byteLength']:
            raise ValueError('Incomplete texture data.')
        (folder/relative).write_bytes(data)
        images[index] = relative
    def texture(info, channel, srgb):
        if info is None:
            return None
        source_index = document['textures'][info['index']]['source']
        return {'file': images[source_index], 'channel': channel, 'sRGB': srgb,
                'tex_coord': info.get('texCoord', 0)}
    plans, review = [], False
    materials = document.get('materials', [])
    for index, material in enumerate(obj.data.materials):
        matches = [m for m in materials if m.get('name') == material.name]
        original = matches[0] if len(matches) == 1 else materials[index] if index < len(materials) else {}
        review |= len(matches) != 1
        pbr = original.get('pbrMetallicRoughness', {})
        plans.append({'slot': index, 'name': f'M_Asset_{index:02d}', 'source_name': material.name,
                      'two_sided': bool(original.get('doubleSided', False)),
                      'base_color': texture(pbr.get('baseColorTexture'), 'RGB', True),
                      'base_color_factor': pbr.get('baseColorFactor', [1, 1, 1, 1]),
                      'roughness': texture(pbr.get('metallicRoughnessTexture'), 'G', False),
                      'roughness_factor': pbr.get('roughnessFactor', 1),
                      'metallic': texture(pbr.get('metallicRoughnessTexture'), 'B', False),
                      'metallic_factor': pbr.get('metallicFactor', 1),
                      'normal': texture(original.get('normalTexture'), 'RGB', False),
                      'extensions': original.get('extensions', {})})
        review |= bool(original.get('extensions')) or original.get('alphaMode', 'OPAQUE') != 'OPAQUE'
        review |= any(original.get('emissiveFactor', [0, 0, 0])) or bool(original.get('occlusionTexture'))
        review |= original.get('normalTexture', {}).get('scale', 1) != 1
        for info in (pbr.get('baseColorTexture'), pbr.get('metallicRoughnessTexture'), original.get('normalTexture')):
            if info:
                review |= info.get('texCoord', 0) != 0 or bool(info.get('extensions'))
    save_json(folder/'material-plan.json', {'slots': plans, 'mapping_review_required': bool(review),
              'instruction': 'Create Unreal materials explicitly; use packed G for roughness/B for metallic. Apply factors. Do not rely on FBX PBR conversion.'})


def export(args):
    bpy.ops.wm.open_mainfile(filepath=str(args.output/'cleaned.blend'))
    obj = bpy.data.objects['SM_Asset']
    collection = bpy.data.collections['Unreal export candidate']
    plan = json.loads((args.output/'material-plan.json').read_bytes())
    for index, original in enumerate(list(obj.data.materials)):
        material = original.copy()
        material.name = f'M_Asset_{index:02d}'
        obj.data.materials[index] = material
        plan['slots'][index]['source_name'] = original.name
        plan['slots'][index]['name'] = material.name
    save_json(args.output/'material-plan.json', plan)
    collision = json.loads((args.output/'collisions.json').read_bytes())
    if not 1 <= len(collision['hulls']) <= 32:
        raise ValueError('Invalid hull count.')
    hulls = []
    for index, hull in enumerate(collision['hulls']):
        name = f'UCX_SM_Asset_{index:02d}'
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(hull['vertices'], [], hull['faces'])
        mesh.update()
        stats = mesh_stats(mesh)
        if stats['nonmanifold_edges'] or stats['volume_m3'] <= 1e-10:
            raise ValueError('Collision hull is not closed with positive volume.')
        points = np.asarray(hull['vertices'])
        for face in mesh.polygons:
            anchor = points[face.vertices[0]]
            if ((points-anchor) @ np.array(face.normal)).max() > 1e-5:
                raise ValueError('Non-convex collision piece.')
        piece = bpy.data.objects.new(name, mesh)
        collection.objects.link(piece)
        piece.display_type = 'WIRE'
        piece.show_in_front = True
        piece.hide_render = True
        piece['method'] = 'Automatic convex proxy; inspect fit and gaps before physics.'
        hulls.append(piece)
    bpy.ops.object.select_all(action='DESELECT')
    for item in [obj, *hulls]:
        item.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(filepath=str(args.output/'asset.fbx'), check_existing=False,
                            use_selection=True, use_visible=False, object_types={'MESH'},
                            global_scale=1, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE',
                            axis_forward='-Y', axis_up='Z', use_mesh_modifiers=True, use_triangles=True,
                            bake_anim=False, add_leaf_bones=False, path_mode='STRIP', embed_textures=False)
    report = json.loads((args.output/'report.json').read_bytes())
    report.update(stage='unreal_import_candidate', collision_mesh_created=True,
                  hull_count=len(hulls), hull_names=[o.name for o in hulls],
                  collision_method={k: v for k, v in collision.items() if k != 'hulls'},
                  collision_volume_m3=sum(h['volume_m3'] for h in collision['hulls']),
                  pivot_review_required=True, orientation_review_required=True,
                  visual_review_required=True, unreal_import_verified=False,
                  unreal_collision_cooking_verified=False, room_compatible=False,
                  preparation_transport='mcp_stdio')
    report['fbx_roundtrip'] = roundtrip(args.output/'asset.fbx', obj, hulls)
    save_json(args.output/'report.json', report)
    # Preview helpers are excluded from export and are useful on opening the .blend.
    scene = bpy.context.scene
    low, high = bounds(obj)
    center = Vector(tuple((low+high)*.5))
    span = float((high-low).max())
    bpy.ops.object.camera_add(location=center+Vector((span*1.8, -span*2.5, span*1.5)))
    camera = bpy.context.object
    camera.rotation_euler = (center-camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.type = 'ORTHO'
    camera.data.ortho_scale = span*1.5
    scene.camera = camera
    for location in ((2, -3, 4), (-3, -1, 2)):
        bpy.ops.object.light_add(type='AREA', location=center+Vector(location)*span)
        light = bpy.context.object
        light.data.energy = 600*span*span
        light.data.shape = 'DISK'
        light.data.size = span*3
        light.rotation_euler = (center-light.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 12
    scene.render.resolution_x = 640
    scene.render.resolution_y = 640
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(args.output/'preview.png')
    scene.world = bpy.data.worlds.new('Review background')
    scene.world.color = (.15, .15, .15)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output/'furniture-unreal.blend'))
    bpy.ops.render.render(write_still=True)
    files = ['asset.fbx', 'report.json', 'material-plan.json', 'furniture-unreal.blend', 'preview.png']
    files += [str(p.relative_to(args.output)).replace('\\', '/') for p in (args.output/'textures').glob('*')]
    save_json(args.output/'export-manifest.json', {'stage': 'unreal_import_candidate',
              'files': {name: sha(args.output/name) for name in files},
              'review_required': True, 'blender_version': bpy.app.version_string})


def roundtrip(path, source, hulls):
    scene = bpy.context.window.scene
    original_materials = set(bpy.data.materials)
    original_images = set(bpy.data.images)
    expected = {o.name for o in [source, *hulls]}
    low, high = bounds(source)
    temp = bpy.data.scenes.new('Export verification')
    bpy.context.window.scene = temp
    imported = []
    try:
        bpy.ops.import_scene.fbx(filepath=str(path))
        imported = list(temp.objects)
        # Blender suffixes reimported objects because the source names still exist.
        names = {o.name.split('.')[0] for o in imported if o.type == 'MESH'}
        if names != expected or len(imported) != len(expected):
            raise ValueError('FBX roundtrip lost render/collision geometry.')
        render = next(o for o in imported if o.name.split('.')[0] == 'SM_Asset')
        actual_low, actual_high = bounds(render)
        if not np.allclose(low, actual_low, atol=1e-4) or not np.allclose(high, actual_high, atol=1e-4):
            raise ValueError('FBX roundtrip changed scale or orientation.')
        if len(render.data.materials) != len(source.data.materials) or len(render.data.uv_layers) != len(source.data.uv_layers):
            raise ValueError('FBX roundtrip lost materials or UV layers.')
        return {'meshes': len(expected), 'hulls': len(hulls), 'bounds_within_0_1_mm': True,
                'material_slots': len(render.data.materials), 'uv_layers': len(render.data.uv_layers)}
    finally:
        bpy.context.window.scene = scene
        for obj in imported:
            mesh = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if isinstance(mesh, bpy.types.Mesh) and mesh.users == 0:
                bpy.data.meshes.remove(mesh)
        for material in set(bpy.data.materials)-original_materials:
            if material.users == 0:
                bpy.data.materials.remove(material)
        for image in set(bpy.data.images)-original_images:
            if image.users == 0:
                bpy.data.images.remove(image)
        bpy.data.scenes.remove(temp)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('cleanup', 'export'))
    parser.add_argument('--source', type=Path)
    parser.add_argument('--request', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--yaw', type=int, choices=(0, 90, 180, 270), default=0)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    cleanup(args) if args.stage == 'cleanup' else export(args)
