"""Blender 5.1 room assembler. Call assemble(package_dir, chair_blend, output_blend).
Builds separate review scenes from hash-checked spatial JSON; never edits source files.
"""
import hashlib
import json
import math
from pathlib import Path


def assemble(package_dir, chair_blend, output_blend):
    import bpy
    from mathutils import Vector
    folder, source, output = (Path(p).resolve() for p in (package_dir, chair_blend, output_blend))
    if output.exists():
        raise RuntimeError('Choose a new output filename; overwrite is refused.')
    manifest = json.loads((folder/'manifest.json').read_text())
    if manifest.get('stage') != 'spatial_drafts_ready':
        raise RuntimeError('Expected spatial drafts package.')
    specs = []
    for name, expected in manifest['files_sha256'].items():
        if name.startswith('room_') and name.endswith('.json'):
            path = folder/name
            if path.parent != folder or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise RuntimeError('Room specification hash mismatch: ' + name)
            spec = json.loads(path.read_text())
            if spec.get('units') != 'metres' or spec.get('up_axis') != 'Z':
                raise RuntimeError('Unsupported unit/axis convention.')
            specs.append(spec)
    specs.sort(key=lambda s: s['scene_id'])
    if len(specs) != manifest['scene_count'] or not specs:
        raise RuntimeError('Missing room specifications.')
    # All destructive setup is restricted to the new output session. Save current work first.
    if bpy.data.is_dirty:
        raise RuntimeError('Save the current Blender file before assembly.')
    with bpy.data.libraries.load(str(source), link=False) as (available, requested):
        names = [n for n in available.objects if n == 'SM_Chair_Demo' or n.startswith('UCX_SM_Chair_Demo_')]
        if len(names) != 20:
            raise RuntimeError('Expected prepared chair plus 19 collision pieces.')
        requested.objects = names
    templates = {o.name: o for o in requested.objects}
    render = templates['SM_Chair_Demo']
    if render.modifiers:
        raise RuntimeError('Prepared chair must have no live modifiers.')
    coordinates = [render.matrix_world @ Vector(c) for c in render.bound_box]
    bounds = [[min(v[i] for v in coordinates) for i in range(3)],
              [max(v[i] for v in coordinates) for i in range(3)]]
    if abs(bounds[0][2]) > .001 or abs(bounds[1][2]-1) > .01:
        raise RuntimeError('Chair scale/pivot is not the reviewed one-metre asset.')
    def material(name, color):
        m = bpy.data.materials.new(name)
        m.diffuse_color = (*color, 1)
        m.use_nodes = True
        m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value = (*color, 1)
        m.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value = .7
        return m
    wallmat = material('POC room plaster', (.57, .63, .66))
    floormat = material('POC room floor', (.23, .28, .30))
    green = material('POC aisle guide', (.05, .5, .32))
    red = material('POC obstruction guide', (.7, .10, .05))
    white = material('POC lettering', (.95, .95, .9))
    def cube(collection, name, position, dimensions, mat):
        x, y, z = (d/2 for d in dimensions)
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata([(-x,-y,-z),(-x,-y,z),(-x,y,-z),(-x,y,z),
                          (x,-y,-z),(x,-y,z),(x,y,-z),(x,y,z)], [],
                         [(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)])
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        collection.objects.link(obj)
        obj.location = position
        obj.data.materials.append(mat)
        return obj
    def text(collection, name, body, location, size):
        data = bpy.data.curves.new(name, 'FONT')
        data.body, data.size, data.align_x = body, size, 'CENTER'
        obj = bpy.data.objects.new(name, data)
        collection.objects.link(obj)
        obj.location = location
        data.materials.append(white)
        obj['role'] = 'review_annotation_only'
    def camera(scene, location, target, ortho):
        data = bpy.data.cameras.new(scene.name+' camera')
        data.type, data.ortho_scale = 'ORTHO', ortho
        obj = bpy.data.objects.new(data.name, data)
        scene.collection.objects.link(obj)
        obj.location = location
        obj.rotation_euler = (Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
        scene.camera = obj
        scene.render.engine = 'CYCLES'
        scene.cycles.samples = 16
        scene.render.resolution_x, scene.render.resolution_y = 1500, 900
        scene.render.resolution_percentage = 100
        world = bpy.data.worlds.new(scene.name+' world')
        world.use_nodes = True
        world.node_tree.nodes['Background'].inputs['Color'].default_value = (.65,.75,.85,1)
        world.node_tree.nodes['Background'].inputs['Strength'].default_value = .7
        scene.world = world
        light = bpy.data.lights.new(scene.name+' area', 'AREA')
        light.energy, light.shape, light.size = 2200, 'DISK', 8
        obj = bpy.data.objects.new(light.name, light)
        scene.collection.objects.link(obj)
        obj.location = (0,4,10)
    report = {'stage': 'blender_assembled_review_required', 'chair_source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'chair_bounds_m': bounds, 'rooms': [], 'unreal_assembled': False,
              'physical_properties_calibrated': False, 'construction': 'procedural from ARC scene specifications'}
    collections = []
    for spec in specs:
        scene = bpy.data.scenes.new('POC_'+spec['scene_id'])
        scene.unit_settings.system, scene.unit_settings.scale_length = 'METRIC', 1
        collection = bpy.data.collections.new(spec['scene_id']+' room')
        scene.collection.children.link(collection)
        collections.append(collection)
        w, d, h = (spec['room'][key] for key in ('width_m','depth_m','height_m'))
        door = spec['room']['door']
        gap, dh = door['width_m'], door['height_m']
        cube(collection, 'Floor', (0,d/2,-.1), (w+.3,d+.3,.2), floormat)
        for x in (-w/2-.075,w/2+.075):
            cube(collection, 'Side wall', (x,d/2,h/2), (.15,d,h), wallmat)
        front = cube(collection, 'Front wall - hidden for cutaway review', (0,-.075,h/2), (w,.15,h), wallmat)
        front.hide_render = True
        front.hide_viewport = True
        front['cutaway_review_only'] = True
        segment = (w-gap)/2
        for sign in (-1,1):
            cube(collection, 'Exit wall side', (sign*(gap/2+segment/2),d+.075,h/2), (segment,.15,h), wallmat)
        cube(collection, 'Door lintel', (0,d+.075,dh+(h-dh)/2), (gap,.15,h-dh), wallmat)
        # A real empty opening below the lintel, not a texture painted onto a solid wall.
        aisle = spec['designated_aisle']['bounds_xy_m']
        guide = cube(collection, 'Aisle overlay - annotation only', (0,(aisle[1]+aisle[3])/2,.003),
                     (aisle[2]-aisle[0],aisle[3]-aisle[1],.004), green)
        guide['role'] = 'review_annotation_only'
        text(collection, 'Exit label', 'EXIT', (0,d-.35,.012), .3)
        text(collection, 'Room label', spec['scene_id']+' / '+spec['designated_aisle']['condition'], (0,-.7,.012), .32)
        chair_count = 0
        for item in spec['objects']:
            if item['asset_id'] != 'hunyuan_wooden_chair_8053348':
                raise RuntimeError('Unbound asset ID.')
            base = bpy.data.objects.new(item['instance_id'], None)
            collection.objects.link(base)
            base.location = item['position_m']
            r = item['rotation_degrees']
            base.rotation_euler = tuple(math.radians(r[k]) for k in ('roll','pitch','yaw'))
            base.scale = item['scale']
            base['asset_id'] = item['asset_id']
            for name, template in templates.items():
                obj = bpy.data.objects.new(item['instance_id']+'__'+name, template.data)
                collection.objects.link(obj)
                obj.parent = base
                obj.matrix_basis = template.matrix_world.copy()
                collider = name.startswith('UCX_')
                obj.hide_render = collider
                obj.hide_viewport = collider
                obj['role'] = 'convex_collision_candidate' if collider else 'render_mesh'
                if not collider:
                    chair_count += 1
                    # matrix_world readback happens after dependency graph update below.
            if item['instance_id'] in spec['designated_aisle']['overlapping_instances']:
                x,y,_ = item['position_m']
                marker = cube(collection,'Obstruction footprint guide',(x,y,.009),(.64,.73,.006),red)
                marker['role'] = 'review_annotation_only'
        camera(scene, (10,-11,13), (0,4,0), 13)
        report['rooms'].append({'scene_id': spec['scene_id'], 'spec_sha256': hashlib.sha256((folder/(spec['scene_id']+'.json')).read_bytes()).hexdigest(),
             'chair_count': chair_count, 'collider_count': chair_count*19,
             'doorway_opening_m': [gap,dh], 'front_wall_hidden_for_review': True})
    overview = bpy.data.scenes.new('POC_00_Overview')
    for i, collection in enumerate(collections):
        obj = bpy.data.objects.new('Overview '+collection.name, None)
        obj.instance_type, obj.instance_collection = 'COLLECTION', collection
        obj.location = (i*11,0,0)
        overview.collection.objects.link(obj)
    camera(overview, (11,-20,31), (11,4,0), 36)
    for i in range(1, len(collections)):
        light = bpy.data.lights.new('Overview area '+str(i), 'AREA')
        light.energy, light.shape, light.size = 2200, 'DISK', 8
        obj = bpy.data.objects.new(light.name, light)
        overview.collection.objects.link(obj)
        obj.location = (i*11,4,10)
    bpy.context.window.scene = overview
    bpy.context.view_layer.update()
    for scene, spec in zip([bpy.data.scenes['POC_'+s['scene_id']] for s in specs],specs):
        bpy.context.window.scene = scene
        bpy.context.view_layer.update()
        for item in spec['objects']:
            obj = next(o for o in scene.objects if o.name.startswith(item['instance_id']+'__SM_Chair_Demo'))
            if (obj.matrix_world.translation-Vector(item['position_m'])).length > 1e-5:
                raise RuntimeError('Chair world-position mismatch.')
    bpy.context.window.scene = overview
    for scene in bpy.data.scenes:
        if not scene.name.startswith('POC_'):
            bpy.data.scenes.remove(scene)
    for template in templates.values():
        if template.users == 0:
            bpy.data.objects.remove(template)
    bpy.data.texts.new('POC_room_assembly_report.json').write(json.dumps(report, indent=2))
    for spec in specs:
        bpy.data.texts.new(spec['scene_id']+'.json').write(json.dumps(spec,indent=2))
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces.active.region_3d.view_perspective = 'CAMERA'
                area.spaces.active.shading.type = 'MATERIAL'
    bpy.ops.file.pack_all()
    output.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    return report
