"""Run via Unreal 5.8 File > Execute Python Script, beside the exported FBX.
Creates fresh assets and a new demo map. Does not start simulation.
Engine execution is required to validate this script; never run in Blender.
"""
import hashlib
import json
import traceback
import uuid
from datetime import UTC, datetime
from pathlib import Path


def verify_package(folder):
    """Engine-independent check against the reviewed Blender export manifest."""
    folder = Path(folder).resolve()
    manifest = json.loads((folder / 'export-manifest.json').read_text(encoding='utf-8'))
    required = ['SM_Chair_Demo.fbx', 'material-plan.json',
                'textures/T_Chair_BaseColor.png', 'textures/T_Chair_Roughness.png',
                'textures/T_Chair_Metallic.png']
    if manifest.get('stage') != 'blender_export_complete':
        raise RuntimeError('Expected the completed Blender export package.')
    if len(manifest.get('collision_meshes', [])) != 19:
        raise RuntimeError('Expected a 19-piece collision export.')
    for relative in required:
        entry = manifest.get('files', {}).get(relative)
        if not entry:
            raise RuntimeError('Missing manifest entry: ' + relative)
        path = folder / relative
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
            raise RuntimeError('Missing or changed package file: ' + relative)
    return manifest


def configure_fbx(u):
    options = u.FbxImportUI()
    for name, value in {'import_mesh': True, 'import_as_skeletal': False,
                        'import_materials': False, 'import_textures': False,
                        'import_animations': False,
                        'automated_import_should_detect_type': False,
                        'mesh_type_to_import': u.FBXImportType.FBXIT_STATIC_MESH}.items():
        options.set_editor_property(name, value)
    data = options.get_editor_property('static_mesh_import_data')
    for name, value in {'auto_generate_collision': False, 'one_convex_hull_per_ucx': True,
                        'combine_meshes': False, 'import_uniform_scale': 1.0,
                        'convert_scene': True, 'convert_scene_unit': True,
                        'force_front_x_axis': False, 'generate_lightmap_u_vs': False,
                        'normal_import_method': u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS}.items():
        data.set_editor_property(name, value)
    return options


def import_one(u, tools, assets, file, target, name, options=None, factory=None):
    task = u.AssetImportTask()
    for prop, value in {'filename': str(file), 'destination_path': target,
                        'destination_name': name, 'automated': True,
                        'replace_existing': False, 'save': True}.items():
        task.set_editor_property(prop, value)
    if options is not None:
        task.set_editor_property('options', options)
    if factory is not None:
        task.set_editor_property('factory', factory)
    tools.import_asset_tasks([task])
    paths = task.get_editor_property('imported_object_paths')
    loaded = [assets.load_asset(path) for path in paths]
    if len(loaded) != 1 or loaded[0] is None:
        raise RuntimeError(f'Expected one asset from {file.name}; imported paths: {list(paths)}')
    return loaded[0]


def new_material(u, tools, path, name, color=None, roughness=.5):
    material = tools.create_asset(name, path, u.Material, u.MaterialFactoryNew())
    if material is None:
        raise RuntimeError('Could not create material ' + name)
    editing = u.MaterialEditingLibrary
    if color is not None:
        expression = editing.create_material_expression(material, u.MaterialExpressionConstant3Vector, -400, 0)
        expression.set_editor_property('constant', u.LinearColor(*color[:3], 1))
        if not editing.connect_material_property(expression, '', u.MaterialProperty.MP_BASE_COLOR):
            raise RuntimeError('Base color connection failed: ' + name)
    scalar = editing.create_material_expression(material, u.MaterialExpressionConstant, -400, 180)
    scalar.set_editor_property('r', roughness)
    if not editing.connect_material_property(scalar, '', u.MaterialProperty.MP_ROUGHNESS):
        raise RuntimeError('Roughness connection failed: ' + name)
    return material


def wire_texture(u, material, texture, prop, output, y, is_data=False):
    editing = u.MaterialEditingLibrary
    expression = editing.create_material_expression(material, u.MaterialExpressionTextureSample, -600, y)
    expression.set_editor_property('texture', texture)
    expression.set_editor_property('sampler_type', u.MaterialSamplerType.SAMPLERTYPE_MASKS
                                   if is_data else u.MaterialSamplerType.SAMPLERTYPE_COLOR)
    if not editing.connect_material_property(expression, output, prop):
        raise RuntimeError('Texture connection failed: ' + texture.get_name())


def spawn(u, actor_system, cls, label, location, rotation=None):
    actor = actor_system.spawn_actor_from_class(cls, u.Vector(*location),
                                                rotation or u.Rotator(0, 0, 0))
    if actor is None:
        raise RuntimeError('Could not spawn ' + label)
    actor.set_actor_label(label)
    return actor


def build_scene(u, actor_system, level_system, root, mesh, floor_material, physics_material):
    level_path = root + '/Maps/L_ChairVisualDemo'
    if not level_system.new_level(level_path):
        raise RuntimeError('Could not create the separate demo level.')
    floor = spawn(u, actor_system, u.StaticMeshActor, 'Demo floor', (0, 0, -5))
    fc = floor.get_component_by_class(u.StaticMeshComponent)
    cube = u.load_asset('/Engine/BasicShapes/Cube.Cube')
    if cube is None or not fc.set_static_mesh(cube):
        raise RuntimeError('Engine basic cube mesh unavailable.')
    floor.set_actor_scale3d(u.Vector(14, 14, .1))
    fc.set_material(0, floor_material)
    fc.set_collision_profile_name('BlockAll')
    fc.set_phys_material_override(physics_material)
    chairs = []
    cases = [('Display chair', (-180, 0, 0), u.Rotator(0, 0, 0), False),
             ('Upright drop', (0, 0, 65), u.Rotator(0, 0, 0), True),
             ('Tilted drop', (180, 0, 85), u.Rotator(0, 0, 30), True)]
    for label, location, rotation, simulate in cases:
        actor = spawn(u, actor_system, u.StaticMeshActor, label, location, rotation)
        component = actor.get_component_by_class(u.StaticMeshComponent)
        component.set_mobility(u.ComponentMobility.MOVABLE)
        if not component.set_static_mesh(mesh):
            raise RuntimeError('Chair mesh assignment failed.')
        component.set_collision_profile_name('PhysicsActor' if simulate else 'BlockAll')
        component.set_phys_material_override(physics_material)
        if simulate:
            component.set_mass_override_in_kg('None', 5.0, True)
            component.set_linear_damping(.05)
            component.set_angular_damping(.1)
            component.set_enable_gravity(True)
            component.set_simulate_physics(True)
        chairs.append({'label': label, 'location_cm': list(location),
                       'simulate_physics': simulate, 'mass_kg_assumed': 5.0 if simulate else None})
    # Broad area lights make a neutral studio scene without relying on starter content.
    target = u.Vector(0, 0, 70)
    for label, position, intensity in [('Key light', (150, -250, 340), 12000),
                                        ('Fill light', (-300, -100, 220), 7000),
                                        ('Rim light', (100, 260, 300), 14000)]:
        rotation = u.MathLibrary.find_look_at_rotation(u.Vector(*position), target)
        light = spawn(u, actor_system, u.RectLight, label, position, rotation)
        component = light.get_component_by_class(u.RectLightComponent)
        component.set_mobility(u.ComponentMobility.MOVABLE)
        component.set_editor_property('intensity_units', u.LightUnits.LUMENS)
        component.set_intensity(intensity)
        component.set_editor_property('source_width', 250.0)
        component.set_editor_property('source_height', 250.0)
        component.set_editor_property('attenuation_radius', 1800.0)
    camera_position = u.Vector(390, -660, 330)
    camera = spawn(u, actor_system, u.CameraActor, 'Demo camera',
                   (camera_position.x, camera_position.y, camera_position.z),
                   u.MathLibrary.find_look_at_rotation(camera_position, target))
    camera.get_component_by_class(u.CameraComponent).set_field_of_view(55)
    if not level_system.save_current_level():
        raise RuntimeError('Could not save the demo level.')
    # Viewport conveniences must not turn a saved setup into a failed import.
    try:
        level_system.pilot_level_actor(camera)
    except (AttributeError, RuntimeError) as exc:
        u.log_warning('Scene saved; select Demo camera to inspect it: ' + str(exc))
    return level_path, chairs


def main():
    import unreal as u

    folder = Path(__file__).resolve().parent
    run_id = datetime.now(UTC).strftime('%Y%m%d_%H%M%S') + '_' + uuid.uuid4().hex[:6]
    report_dir = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_saved_dir())) / 'EmergencyPOC'
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / ('chair-setup-' + run_id + '.json')
    report = {'stage': 'preflight', 'engine_version': u.SystemLibrary.get_engine_version(),
              'unreal_setup_executed': True, 'chaos_simulation_observed': False,
              'package_folder': str(folder), 'source_shape_job': '8052814',
              'source_paint_job': '8053348', 'created_content_root': None}
    try:
        if not report['engine_version'].startswith('5.8.'):
            raise RuntimeError('This setup targets Unreal Engine 5.8.x.')
        required = ['FbxFactory', 'FbxImportUI', 'EditorAssetSubsystem', 'StaticMeshEditorSubsystem',
                    'EditorActorSubsystem', 'LevelEditorSubsystem', 'MaterialEditingLibrary',
                    'PhysicalMaterialFactoryNew', 'EditorLoadingAndSavingUtils']
        missing = [name for name in required if not hasattr(u, name)]
        if missing:
            raise RuntimeError('Editor API unavailable: ' + ', '.join(missing))
        manifest = verify_package(folder)
        plan = json.loads((folder / 'material-plan.json').read_text(encoding='utf-8'))
        levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
        if levels.is_in_play_in_editor():
            raise RuntimeError('Stop Play/Simulate before running setup.')
        if u.EditorLoadingAndSavingUtils.get_dirty_map_packages():
            raise RuntimeError('Save your current level first (Ctrl+S), then rerun. No content imported yet.')
        assets = u.get_editor_subsystem(u.EditorAssetSubsystem)
        tools = u.AssetToolsHelpers.get_asset_tools()
        actor_system = u.get_editor_subsystem(u.EditorActorSubsystem)
        root = '/Game/EmergencyPOC/ChairDemo_' + run_id
        if assets.does_directory_exist(root):
            raise RuntimeError('Target content folder unexpectedly already exists.')
        report['created_content_root'] = root
        for suffix in ('/Meshes', '/Textures', '/Materials', '/Maps'):
            if not assets.make_directory(root + suffix):
                raise RuntimeError('Could not create content folder: ' + root + suffix)
        report['stage'] = 'mesh_import'
        world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
        cvar = 'Interchange.FeatureFlags.Import.FBX'
        previous = u.SystemLibrary.get_console_variable_int_value(cvar)
        try:
            # Use explicit legacy FBX options only for this import, then restore cvar.
            u.SystemLibrary.execute_console_command(world, cvar + ' 0')
            mesh = import_one(u, tools, assets, folder / 'SM_Chair_Demo.fbx', root + '/Meshes',
                              'SM_Chair_Demo', configure_fbx(u), u.FbxFactory())
        finally:
            u.SystemLibrary.execute_console_command(world, cvar + ' ' + str(previous))
        if not isinstance(mesh, u.StaticMesh):
            raise TypeError('FBX did not produce a StaticMesh.')
        mesh_editor = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
        hull_count = mesh_editor.get_convex_collision_count(mesh)
        bounds = mesh.get_bounding_box()
        height = bounds.max.z - bounds.min.z
        report.update({'mesh_asset': mesh.get_path_name(), 'convex_collision_count': hull_count,
                       'height_cm': height, 'bottom_z_cm': bounds.min.z})
        if hull_count != 19:
            raise RuntimeError(f'Imported {hull_count} convex hulls; expected 19. Scene not created.')
        if abs(height - manifest['expected_unreal_height_cm']) > 1.0 or abs(bounds.min.z) > .5:
            raise RuntimeError('Imported size/pivot differs from the reviewed one-metre chair.')
        body = mesh.get_editor_property('body_setup')
        body.set_editor_property('collision_trace_flag', u.CollisionTraceFlag.CTF_USE_SIMPLE_AND_COMPLEX)
        report['stage'] = 'textures_materials'
        textures = {}
        for suffix in ('BaseColor', 'Roughness', 'Metallic'):
            name = 'T_Chair_' + suffix
            texture = import_one(u, tools, assets, folder / 'textures' / (name + '.png'),
                                 root + '/Textures', name)
            texture.set_editor_property('srgb', suffix == 'BaseColor')
            if suffix != 'BaseColor':
                texture.set_editor_property('compression_settings', u.TextureCompressionSettings.TC_MASKS)
            if not assets.save_loaded_asset(texture):
                raise RuntimeError('Could not save texture ' + name)
            textures[suffix] = texture
        wood = new_material(u, tools, root + '/Materials', 'M_Chair_Wood')
        wire_texture(u, wood, textures['BaseColor'], u.MaterialProperty.MP_BASE_COLOR, 'RGB', 0)
        wire_texture(u, wood, textures['Roughness'], u.MaterialProperty.MP_ROUGHNESS, 'R', 260, True)
        wire_texture(u, wood, textures['Metallic'], u.MaterialProperty.MP_METALLIC, 'R', 520, True)
        cut_plan = plan['material_slots'][1]
        cut = new_material(u, tools, root + '/Materials', 'M_Chair_CutFaces',
                           cut_plan['base_color_linear_rgba'], cut_plan['roughness'])
        floor_mat = new_material(u, tools, root + '/Materials', 'M_DemoFloor', [.055, .065, .075], .8)
        for material in (wood, cut, floor_mat):
            u.MaterialEditingLibrary.layout_material_expressions(material)
            u.MaterialEditingLibrary.recompile_material(material)
            if not assets.save_loaded_asset(material):
                raise RuntimeError('Could not save material ' + material.get_name())
        slots = mesh.get_editor_property('static_materials')
        if len(slots) != 2:
            raise RuntimeError('Expected exactly two render material slots.')
        slot_report = []
        for index, slot in enumerate(slots):
            name = str(slot.get_editor_property('imported_material_slot_name'))
            if 'cutfaces' in name.lower():
                material = cut
            elif 'wood' in name.lower():
                material = wood
            else:
                raise RuntimeError('Unrecognized imported material slot: ' + name)
            mesh.set_material(index, material)
            slot_report.append({'index': index, 'imported_name': name, 'material': material.get_path_name()})
        if not assets.save_loaded_asset(mesh):
            raise RuntimeError('Could not save configured chair mesh.')
        report['material_slots'] = slot_report
        physics = tools.create_asset('PM_DemoWood', root + '/Materials', u.PhysicalMaterial,
                                     u.PhysicalMaterialFactoryNew())
        if physics is None:
            raise RuntimeError('Could not create the demo physical material.')
        physics.set_editor_property('friction', .55)
        physics.set_editor_property('restitution', .05)
        if not assets.save_loaded_asset(physics):
            raise RuntimeError('Could not save demo physical material.')
        report['stage'] = 'demo_level'
        level_path, cases = build_scene(u, actor_system, levels, root, mesh, floor_mat, physics)
        report.update({'stage': 'setup_complete', 'level_asset': level_path, 'cases': cases,
                       'assumptions': {'dynamic_chair_mass_kg': 5.0, 'friction': .55, 'restitution': .05,
                                       'overall_height_measured': False,
                                       'gravity': 'Uses this project gravity settings; not independently measured.'},
                       'next_action': 'Inspect scene, then Alt+S to Simulate; Esc to stop. Observe and record results.'})
        u.log('POC CHAIR SETUP COMPLETE: ' + level_path)
        u.log('Inspect, then Alt+S to simulate. No simulation has been run by this setup script.')
    except Exception as exc:
        report.update({'stage_failed_at': report['stage'], 'stage': 'failed',
                       'error': str(exc), 'traceback': traceback.format_exc()})
        u.log_error('POC CHAIR SETUP FAILED: ' + str(exc))
        raise
    finally:
        report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
        u.log('POC setup report: ' + str(report_path))


if __name__ == '__main__':
    main()
