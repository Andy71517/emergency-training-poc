"""Blender 5.1.2: reversible, model-specific repair of Hunyuan chair job 8053348.
Run in the Scripting workspace on Andy's scaled chair-cleanup.blend.
Creates a separate preview and hidden source; does not save or overwrite files.
"""
import bpy
import bmesh
import numpy as np

TAG = 'POC_Backrest_Repair'
GAPS = [(-0.181, -0.124), (-0.085, -0.052), (-0.017, 0.022),
        (0.056, 0.091), (0.128, 0.184)]


def topology(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    result = {'vertices': len(bm.verts), 'faces': len(bm.faces),
              'nonmanifold_edges': sum(not e.is_manifold for e in bm.edges)}
    bm.free()
    return result


def main():
    if bpy.context.mode != 'OBJECT':
        raise RuntimeError('Return to Object Mode before running this script.')
    if bpy.data.collections.get(TAG):
        raise RuntimeError('Repair already exists. Reopen the saved input to start again.')
    source = bpy.data.objects.get('chair-textured.obj')
    if source is None or source.type != 'MESH':
        raise RuntimeError('Expected the uploaded chair-cleanup.blend mesh.')
    expected = [(-.267113775, .274810910), (-.420098275, .212417215),
                (-.026568651, .973388314)]
    coords = [source.matrix_world @ v.co for v in source.data.vertices]
    bounds = [(min(v[i] for v in coords), max(v[i] for v in coords)) for i in range(3)]
    if len(source.data.vertices) != 49933 or len(source.data.polygons) != 80000:
        raise RuntimeError('Unexpected mesh counts; this repair is for chair job 8053348 only.')
    if any(abs(bounds[i][j] - expected[i][j]) > .0001 for i in range(3) for j in range(2)):
        raise RuntimeError('Unexpected chair placement/size. No changes were made.')
    collection = bpy.data.collections.new(TAG)
    bpy.context.scene.collection.children.link(collection)
    chair = source.copy()
    chair.data = source.data.copy()
    chair.name = 'Chair_Repaired_Preview'
    chair.parent = None
    chair.matrix_world = source.matrix_world.copy()
    collection.objects.link(chair)
    # Weld coincident UV-split positions on the copy. UVs remain per face corner.
    bm = bmesh.new()
    bm.from_mesh(chair.data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-6)
    bm.to_mesh(chair.data)
    bm.free()
    chair.data.update()
    before = topology(chair.data)
    if before['nonmanifold_edges']:
        raise RuntimeError(f'Copy is not closed before cuts: {before}; original unchanged.')
    # Exact floor correction: move copied vertices, retain origin at world zero.
    lift = -bounds[2][0]
    for vertex in chair.data.vertices:
        vertex.co.z += lift
    chair.data.update()
    material = bpy.data.materials.new('POC cut surfaces - approximate brown wood')
    material.diffuse_color = (.20, .075, .022, 1)
    material.use_nodes = True
    shader = material.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = material.diffuse_color
    shader.inputs['Metallic'].default_value = 0
    shader.inputs['Roughness'].default_value = .55
    chair.data.materials.append(material)
    for index, (left, right) in enumerate(GAPS, 1):
        # Boxes stop inside the rails; generous Y depth spans the tilted backrest.
        z_low, z_high = .546 + lift, .864 + lift
        mesh = bpy.data.meshes.new(f'Gap_{index}_cutter_mesh')
        verts = [(x, y, z) for x in (left, right) for y in (-.5, .5)
                 for z in (z_low, z_high)]
        faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
                 (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
        mesh.from_pydata(verts, [], faces)
        mesh.materials.append(source.data.materials[0])
        mesh.materials.append(material)
        for polygon in mesh.polygons:
            polygon.material_index = 1
        cutter = bpy.data.objects.new(f'Gap_{index}_cutter', mesh)
        collection.objects.link(cutter)
        cutter.display_type = 'WIRE'
        cutter.hide_render = True
        cutter.hide_set(True)
        modifier = chair.modifiers.new(f'Open backrest gap {index}', 'BOOLEAN')
        modifier.operation = 'DIFFERENCE'
        modifier.solver = 'EXACT'
        modifier.object = cutter
        modifier.material_mode = 'INDEX'
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = chair.evaluated_get(depsgraph)
    final_mesh = evaluated.to_mesh()
    after = topology(final_mesh)
    cut_faces = sum(p.material_index == 1 for p in final_mesh.polygons)
    final_min_z = min(v.co.z for v in final_mesh.vertices)
    evaluated.to_mesh_clear()
    if after['nonmanifold_edges'] or not cut_faces or abs(final_min_z) > 1e-5:
        chair.hide_set(True)
        raise RuntimeError(f'Repair validation failed: {after}, cut_faces={cut_faces}. Original remains visible.')
    # Paint correction on a copied albedo: replace pale neutral background remnants.
    # This is an approximate brown fill, not recovered wood texture.
    copied_material = source.data.materials[0].copy()
    copied_material.name = 'POC repaired wood - copied albedo'
    chair.data.materials[0] = copied_material
    shader = copied_material.node_tree.nodes.get('Principled BSDF')
    color_node = shader.inputs['Base Color'].links[0].from_node
    image = color_node.image.copy()
    image.name = 'POC albedo - neutral remnants tinted brown'
    color_node.image = image
    pixels = np.array(image.pixels[:], dtype=np.float32).reshape(-1, 4)
    rgb = pixels[:, :3]
    mask = (rgb.min(axis=1) > .35) & (np.ptp(rgb, axis=1) < .18)
    brightness = rgb[mask].mean(axis=1)
    rgb[mask] = brightness[:, None] * np.array([.55, .28, .10])
    image.pixels.foreach_set(pixels.ravel())
    image.update()
    image.pack()
    chair['albedo_pixels_tinted'] = int(mask.sum())
    source.hide_set(True)
    source.hide_render = True
    bpy.ops.object.select_all(action='DESELECT')
    chair.hide_set(False)
    chair.select_set(True)
    bpy.context.view_layer.objects.active = chair
    chair['source_shape_job'] = '8052814'
    chair['source_paint_job'] = '8053348'
    chair['scale_note'] = 'Assumed demo height 1 m; not a measured physical asset.'
    chair['repair_note'] = 'Five Boolean openings; brown cut surfaces and neutral albedo tint; original hidden.'
    chair['floor_lift_m'] = lift
    print('POC repair preview ready:', before, '->', after,
          'cut faces:', cut_faces, 'floor lift:', lift)
    print('Inspect both sides. Save As chair-repaired-preview.blend to keep the result.')


if __name__ == '__main__':
    main()
