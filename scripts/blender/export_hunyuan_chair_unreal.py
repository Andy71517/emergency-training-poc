"""Blender 5.1.2: export reviewed POC chair + 19 UCX hulls + explicit textures.
Run on chair-collision-complete.blend; writes a NEW unreal-chair-export folder
beside the saved blend, refusing overwrite. Source scene is never saved/edited.
"""
import hashlib
import json
from pathlib import Path

import bpy
import numpy as np

RENDER = 'SM_Chair_Demo'
COLLECTION = 'POC_Complete_Collision_Preview'


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_texture(source, path, channel=None):
    if channel is None:
        image = source.copy()
    else:
        image = bpy.data.images.new('POC temporary scalar export', width=source.size[0],
                                    height=source.size[1], alpha=True, is_data=True)
        pixels = np.array(source.pixels[:], dtype=np.float32).reshape(-1, 4)
        scalar = pixels[:, channel]
        rgba = np.column_stack((scalar, scalar, scalar, np.ones_like(scalar)))
        image.pixels.foreach_set(rgba.ravel())
        image.update()
    try:
        image.filepath_raw = str(path)
        image.file_format = 'PNG'
        image.save()
    finally:
        bpy.data.images.remove(image)


def export(output_dir=None):
    if bpy.context.mode != 'OBJECT':
        raise RuntimeError('Return to Object Mode first.')
    if output_dir is None:
        if not bpy.data.filepath:
            raise RuntimeError('Save the completed blend file before exporting.')
        output_dir = Path(bpy.data.filepath).parent / 'unreal-chair-export'
    output_dir = Path(output_dir).resolve()
    if output_dir.exists():
        raise RuntimeError(f'Export folder already exists; choose a new folder: {output_dir}')
    source = bpy.data.objects.get(RENDER)
    collection = bpy.data.collections.get(COLLECTION)
    if source is None or collection is None:
        raise RuntimeError('Open chair-collision-complete.blend first.')
    colliders = sorted((o for o in collection.objects if o.name.startswith('UCX_' + RENDER + '_')),
                       key=lambda o: o.name)
    if len(colliders) != 19:
        raise RuntimeError('Expected exactly 19 reviewed UCX collision pieces.')
    if source.modifiers:
        raise RuntimeError('Expected the evaluated render copy without live modifiers.')
    used_slots = sorted({p.material_index for p in source.data.polygons})
    if used_slots != [0, 1]:
        raise RuntimeError('Unexpected material assignments.')
    wood = source.data.materials[0]
    cut_shader = source.data.materials[1].node_tree.nodes.get('Principled BSDF')
    images = [n.image for n in wood.node_tree.nodes if n.type == 'TEX_IMAGE']
    albedo = next(i for i in images if i.colorspace_settings.name == 'sRGB')
    mr = next(i for i in images if i.colorspace_settings.name == 'Non-Color')
    if tuple(albedo.size) != (1024, 1024) or tuple(mr.size) != (1024, 1024):
        raise RuntimeError('Unexpected texture dimensions.')
    output_dir.mkdir(parents=True)
    texture_dir = output_dir / 'textures'
    texture_dir.mkdir()
    write_texture(albedo, texture_dir / 'T_Chair_BaseColor.png')
    write_texture(mr, texture_dir / 'T_Chair_Roughness.png', channel=1)
    write_texture(mr, texture_dir / 'T_Chair_Metallic.png', channel=2)
    cut_color = list(cut_shader.inputs['Base Color'].default_value)
    cut_roughness = float(cut_shader.inputs['Roughness'].default_value)
    original_scene = bpy.context.window.scene
    temp_scene = bpy.data.scenes.new('POC temporary FBX export')
    temp_scene.unit_settings.system = 'METRIC'
    temp_scene.unit_settings.scale_length = 1.0
    temporary_objects, temporary_materials = [], []
    try:
        bpy.context.window.scene = temp_scene
        for src in [source, *colliders]:
            obj = bpy.data.objects.new(src.name + '_TEMP', src.data.copy())
            obj.matrix_world = src.matrix_world.copy()
            obj['fbx_target_name'] = src.name
            temp_scene.collection.objects.link(obj)
            temporary_objects.append(obj)
        # FBX exporter uses object names. Temporarily lease names, restoring in finally.
        source_names = {o: o.name for o in [source, *colliders]}
        for obj in source_names:
            obj.name = obj.name + '_SOURCE_BACKUP'
        for obj, name in zip(temporary_objects, source_names.values()):
            obj.name = name
        mesh = temporary_objects[0].data
        mesh.materials.clear()
        for name, color, roughness in [('M_Chair_Wood', (1, 1, 1, 1), .5),
                                        ('M_Chair_CutFaces', cut_color, cut_roughness)]:
            mat = bpy.data.materials.new(name)
            mat.use_nodes = True
            shader = mat.node_tree.nodes.get('Principled BSDF')
            shader.inputs['Base Color'].default_value = color
            shader.inputs['Roughness'].default_value = roughness
            shader.inputs['Metallic'].default_value = 0
            mesh.materials.append(mat)
            temporary_materials.append(mat)
        # Clearing slots resets polygon assignments; restore them explicitly.
        for target, src in zip(mesh.polygons, source.data.polygons):
            target.material_index = src.material_index
        for obj in temporary_objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = temporary_objects[0]
        bpy.ops.export_scene.fbx(
            filepath=str(output_dir / (RENDER + '.fbx')), check_existing=False,
            use_selection=True, use_visible=False, object_types={'MESH'},
            global_scale=1.0, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE',
            axis_forward='-Y', axis_up='Z', use_space_transform=True,
            bake_space_transform=False, use_mesh_modifiers=True, use_triangles=True,
            mesh_smooth_type='FACE', use_tspace=True, bake_anim=False,
            add_leaf_bones=False, path_mode='STRIP', embed_textures=False,
            use_custom_props=False,
        )
    finally:
        bpy.context.window.scene = original_scene
        for obj in temporary_objects:
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if data.users == 0:
                bpy.data.meshes.remove(data)
        if 'source_names' in locals():
            for obj, name in source_names.items():
                obj.name = name
        for mat in temporary_materials:
            if mat.users == 0:
                bpy.data.materials.remove(mat)
        bpy.data.scenes.remove(temp_scene)
    material_plan = {
        'material_slots': [
            {'index': 0, 'name': 'M_Chair_Wood',
             'base_color': {'file': 'textures/T_Chair_BaseColor.png', 'sRGB': True},
             'roughness': {'file': 'textures/T_Chair_Roughness.png', 'sRGB': False,
                           'compression': 'Masks', 'channel': 'R'},
             'metallic': {'file': 'textures/T_Chair_Metallic.png', 'sRGB': False,
                          'compression': 'Masks', 'channel': 'R'}},
            {'index': 1, 'name': 'M_Chair_CutFaces', 'base_color_linear_rgba': cut_color,
             'roughness': cut_roughness, 'metallic': 0},
        ],
        'normal_map': None, 'ambient_occlusion_map': None,
        'note': 'Explicitly create/connect materials in Unreal; do not rely on FBX material conversion.',
    }
    (output_dir / 'material-plan.json').write_text(json.dumps(material_plan, indent=2), encoding='utf-8')
    collision_report = bpy.data.texts.get('POC_collision_report.json')
    if collision_report:
        (output_dir / 'blender-collision-report.json').write_text(collision_report.as_string(), encoding='utf-8')
    readme = '''# POC chair export for Unreal

One render mesh (SM_Chair_Demo) plus 19 matching UCX convex collision meshes.
Generated from the reviewed Blender 5.1.2 chair. This package has NOT been imported
or simulated in Unreal yet. Blender dimensions are metres; intended Unreal height
is approximately 100 cm with import scale 1. Verify dimensions after import.

## Import checkpoint
- Import SM_Chair_Demo.fbx as one Static Mesh (not skeletal, not Import Into Level).
- Use the supplied named UCX pieces; disable automatic/missing collision generation.
- Keep one convex hull per UCX piece. Verify 19 simple collision elements after import.
- Import scale 1; convert scene/units enabled. Verify Z up, floor pivot, and ~100 cm height.
- Disable material/texture auto-import. Import the three PNGs separately and create
  two materials using material-plan.json. Base color is sRGB; roughness/metallic are
  linear mask data. Both mask textures use their R channel.
- Use simple collision for physics. Do not use Complex As Simple for this dynamic asset.
- Keep actor scale (1,1,1). No mass/friction/inertia settings are inferred from the mesh.
Exact menus depend on Unreal version and its FBX importer. Confirm version before setup.

The old manual boxes, hidden original chair, Boolean cutters, cameras and lights
are excluded. The FBX has two used material slots. The Blender source is unchanged.

## Provenance
Input chair image -> VT ARC Hunyuan3D 2.1 shape run 8052814 -> paint run 8053348 ->
Blender backrest repair/neutral texture tint -> reviewed convex collision preview.
Hunyuan shape revision 07d6dc9694e0ea942683bf6e3e374887d9f5b054;
paint revision 0b94677654c57bb9a6b6845cd7b704ccf551d327;
source revision 82920d643c0dc2f7bfd7255f45f62d386edfe60c.
Model and source terms: https://huggingface.co/tencent/Hunyuan3D-2.1 and
https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1 .
Scale/flat feet are demo assumptions. No structural or real-world physics validation.
'''
    (output_dir / 'README.md').write_text(readme, encoding='utf-8')
    files = {str(p.relative_to(output_dir)): {'bytes': p.stat().st_size, 'sha256': sha256(p)}
             for p in sorted(output_dir.rglob('*')) if p.is_file()}
    manifest = {'stage': 'blender_export_complete', 'blender': bpy.app.version_string,
                'render_mesh': RENDER, 'collision_meshes': [o.name for o in colliders],
                'expected_unreal_height_cm': 99.9956965, 'unreal_import_verified': False,
                'chaos_simulation_verified': False, 'files': files}
    (output_dir / 'export-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print('EXPORT COMPLETE:', output_dir)
    return output_dir


if __name__ == '__main__':
    export()
