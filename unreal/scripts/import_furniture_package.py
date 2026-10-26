"""Execute in Unreal 5.8 from an extracted FIELDWORK furniture package.

Imports into a new content folder, validates hull count/size, and wires supported
PBR materials. Does not place actors, simulate, or certify generated collision fit.
"""
import hashlib
import json
import math
import runpy
import uuid
from pathlib import Path


def verify_package(folder):
    folder = Path(folder).resolve()
    manifest = json.loads((folder/'export-manifest.json').read_bytes())
    if manifest.get('stage') != 'unreal_import_candidate':
        raise ValueError('Expected a completed FIELDWORK export candidate.')
    required = {'asset.fbx', 'report.json', 'material-plan.json', 'setup_unreal58_chair_demo.py'}
    if not required <= set(manifest.get('files', {})):
        raise ValueError('Incomplete Unreal import package.')
    for name, digest in manifest['files'].items():
        path = (folder/name).resolve()
        if not path.is_relative_to(folder) or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('Missing or changed export file: '+name)
    report = json.loads((folder/'report.json').read_bytes())
    plan = json.loads((folder/'material-plan.json').read_bytes())
    if report.get('collision_mesh_created') is not True or not 1 <= report.get('hull_count', 0) <= 32:
        raise ValueError('Expected validated convex collision pieces.')
    if plan.get('mapping_review_required'):
        raise ValueError('This material mapping needs review before automatic Unreal setup.')
    for slot in plan['slots']:
        for field in ('base_color', 'roughness', 'metallic', 'normal'):
            texture = slot.get(field)
            if texture and (texture.get('file') not in manifest['files'] or not texture['file'].startswith('textures/')):
                raise ValueError('Material refers to an unbound texture.')
    return report, plan


def connect(u, material, prop, source, factor, folder, root, helper, textures):
    edit = u.MaterialEditingLibrary
    if source:
        key = (source['file'], source['sRGB'], prop == u.MaterialProperty.MP_NORMAL)
        if key not in textures:
            texture = helper['import_one'](u, u.AssetToolsHelpers.get_asset_tools(),
                u.get_editor_subsystem(u.EditorAssetSubsystem), folder/source['file'],
                root+'/Textures', 'T_Furniture_'+str(len(textures)))
            texture.set_editor_property('srgb', source['sRGB'])
            if not source['sRGB']:
                texture.set_editor_property('compression_settings', u.TextureCompressionSettings.TC_NORMALMAP
                    if key[2] else u.TextureCompressionSettings.TC_MASKS)
            u.EditorAssetLibrary.save_loaded_asset(texture)
            textures[key] = texture
        expression = edit.create_material_expression(material, u.MaterialExpressionTextureSample, -600, 0)
        expression.set_editor_property('texture', textures[key])
        expression.set_editor_property('sampler_type', u.MaterialSamplerType.SAMPLERTYPE_NORMAL if key[2]
            else u.MaterialSamplerType.SAMPLERTYPE_COLOR if source['sRGB'] else u.MaterialSamplerType.SAMPLERTYPE_MASKS)
        output = source['channel']
    else:
        expression = None
        output = ''
    if factor is not None:
        if isinstance(factor, list):
            if len(factor) != 4 or any(not isinstance(n, (int, float)) or not math.isfinite(n) for n in factor):
                raise ValueError('Invalid base color factor.')
            value = edit.create_material_expression(material, u.MaterialExpressionConstant3Vector, -600, 200)
            value.set_editor_property('constant', u.LinearColor(r=factor[0], g=factor[1], b=factor[2], a=1))
        else:
            if not isinstance(factor, (int, float)) or not math.isfinite(factor):
                raise ValueError('Invalid material scalar.')
            value = edit.create_material_expression(material, u.MaterialExpressionConstant, -600, 200)
            value.set_editor_property('r', factor)
        if expression:
            product = edit.create_material_expression(material, u.MaterialExpressionMultiply, -250, 0)
            if not edit.connect_material_expressions(expression, output, product, 'A') or not edit.connect_material_expressions(value, '', product, 'B'):
                raise ValueError('Could not connect material factors.')
            expression = product
        else:
            expression = value
        output = ''
    if expression and not edit.connect_material_property(expression, output, prop):
        raise ValueError('Could not connect a material property.')


def main():
    import unreal as u
    if not u.SystemLibrary.get_engine_version().startswith('5.8.'):
        raise ValueError('This import script targets Unreal Engine 5.8.x.')
    folder = Path(__file__).resolve().parent
    report, plan = verify_package(folder)
    helper = runpy.run_path(str(folder/'setup_unreal58_chair_demo.py'), run_name='fieldwork_import_helper')
    root = '/Game/FIELDWORK/Furniture_'+uuid.uuid4().hex[:10]
    tools = u.AssetToolsHelpers.get_asset_tools()
    assets = u.get_editor_subsystem(u.EditorAssetSubsystem)
    for suffix in ('/Meshes', '/Textures', '/Materials'):
        if not assets.make_directory(root+suffix):
            raise ValueError('Could not create the new asset directory.')
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    # The verified legacy UCX importer is used only for this operation.
    flag = u.SystemLibrary.get_console_variable_int_value('Interchange.FeatureFlags.Import.FBX')
    try:
        u.SystemLibrary.execute_console_command(world, 'Interchange.FeatureFlags.Import.FBX 0')
        mesh = helper['import_one'](u, tools, assets, folder/'asset.fbx', root+'/Meshes', 'SM_Asset',
                                   helper['configure_fbx'](u), u.FbxFactory())
    finally:
        u.SystemLibrary.execute_console_command(world, 'Interchange.FeatureFlags.Import.FBX '+str(flag))
    if not isinstance(mesh, u.StaticMesh):
        raise TypeError('FBX import did not return one StaticMesh.')
    body = mesh.get_editor_property('body_setup')
    hull_count = u.get_editor_subsystem(u.StaticMeshEditorSubsystem).get_convex_collision_count(mesh)
    if hull_count != report['hull_count']:
        raise ValueError('Unreal did not import the expected number of convex pieces.')
    bounds = mesh.get_bounding_box()
    size = bounds.max-bounds.min
    actual = [size.x, size.y, size.z]
    if any(abs(cm-m*100) > .5 for cm, m in zip(actual, report['staged_dimensions_m'])):
        raise ValueError('Unreal mesh dimensions differ from the Blender report.')
    body.set_editor_property('collision_trace_flag', u.CollisionTraceFlag.CTF_USE_SIMPLE_AND_COMPLEX)
    slots = mesh.get_editor_property('static_materials')
    if len(slots) != len(plan['slots']):
        raise ValueError('Imported material slot count differs.')
    textures = {}
    for index, slot in enumerate(slots):
        imported_name = str(slot.get_editor_property('imported_material_slot_name'))
        matches = [p for p in plan['slots'] if p['name'] == imported_name]
        if len(matches) != 1:
            raise ValueError('Cannot identify imported material slot: '+imported_name)
        spec = matches[0]
        material = tools.create_asset('M_Furniture_'+str(index), root+'/Materials', u.Material, u.MaterialFactoryNew())
        if material is None:
            raise ValueError('Could not create a new furniture material.')
        material.set_editor_property('two_sided', spec.get('two_sided', False))
        for prop, source, factor in [
                (u.MaterialProperty.MP_BASE_COLOR, spec['base_color'], spec['base_color_factor']),
                (u.MaterialProperty.MP_ROUGHNESS, spec['roughness'], spec['roughness_factor']),
                (u.MaterialProperty.MP_METALLIC, spec['metallic'], spec['metallic_factor']),
                (u.MaterialProperty.MP_NORMAL, spec['normal'], None)]:
            connect(u, material, prop, source, factor, folder, root, helper, textures)
        u.MaterialEditingLibrary.recompile_material(material)
        assets.save_loaded_asset(material)
        mesh.set_material(index, material)
    assets.save_loaded_asset(mesh)
    evidence = {'stage': 'unreal_asset_imported', 'mesh': mesh.get_path_name(), 'hulls': hull_count,
                'dimensions_cm': actual, 'physics_validated': False,
                'next_step': 'Inspect materials and collision fit; then run an appropriate Chaos contact test.'}
    output = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_saved_dir()))/'FIELDWORK'
    output.mkdir(exist_ok=True)
    (output/('asset-import-'+uuid.uuid4().hex+'.json')).write_text(json.dumps(evidence, indent=2))
    u.log('FIELDWORK furniture imported: '+mesh.get_path_name()+'. Visual/collision review and physics remain required.')


if __name__ == '__main__':
    main()
