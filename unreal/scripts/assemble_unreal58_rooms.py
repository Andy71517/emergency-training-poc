"""Run in Unreal 5.8 with a saved chair demo open. Creates three new room maps.
Consumes hash-bound Blender-reviewed scene JSON. No model calls, imports, or simulation start.
"""
import hashlib
import json
import math
import traceback
import uuid
from datetime import UTC, datetime
from pathlib import Path


def read_specs(folder):
    folder = Path(folder)
    binding = json.loads((folder/'room-package.json').read_text())
    specs = []
    for entry in binding['rooms']:
        path = folder/entry['file']
        if path.parent != folder or hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
            raise RuntimeError('Room JSON is missing or changed: ' + entry['file'])
        spec = json.loads(path.read_text())
        if spec['units'] != 'metres' or spec['up_axis'] != 'Z':
            raise RuntimeError('Expected metres/Z-up.')
        if any(o['rotation_degrees'] != {'pitch':0,'yaw':0,'roll':0} or o['scale'] != [1,1,1] for o in spec['objects']):
            raise RuntimeError('This reviewed batch expects upright, unit-scale chairs.')
        specs.append(spec)
    if len(specs) != 3:
        raise RuntimeError('Expected three reviewed rooms.')
    return binding, specs


def cm(position):
    if len(position) != 3 or any(not math.isfinite(v) for v in position):
        raise ValueError('Invalid metre position.')
    return tuple(float(v)*100 for v in position)


def main():
    import unreal as u
    stamp = datetime.now(UTC).strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:6]
    reports = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_saved_dir()))/'EmergencyPOC'
    reports.mkdir(parents=True,exist_ok=True)
    report = {'stage':'preflight','maps':[], 'simulation_observed':False,
              'physics_calibrated':False,'source':'Blender-reviewed ARC spatial batch'}
    try:
        if not u.SystemLibrary.get_engine_version().startswith('5.8.'):
            raise RuntimeError('This script targets Unreal 5.8.x.')
        binding, specs = read_specs(Path(__file__).resolve().parent)
        levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
        actors = u.get_editor_subsystem(u.EditorActorSubsystem)
        assets = u.get_editor_subsystem(u.EditorAssetSubsystem)
        if levels.is_in_play_in_editor():
            raise RuntimeError('Press Esc to stop simulation first.')
        if u.EditorLoadingAndSavingUtils.get_dirty_map_packages():
            raise RuntimeError('Save current level (Ctrl+S), then rerun.')
        source_actors = [a for a in actors.get_all_level_actors() if a.get_actor_label()=='Display chair']
        if len(source_actors) != 1:
            raise RuntimeError('Open the original or presentation chair demo, with its Display chair actor.')
        mesh = source_actors[0].get_component_by_class(u.StaticMeshComponent).get_editor_property('static_mesh')
        hulls = u.get_editor_subsystem(u.StaticMeshEditorSubsystem).get_convex_collision_count(mesh)
        box = mesh.get_bounding_box()
        if hulls != 19 or abs(box.max.z-box.min.z-100) > 1 or abs(box.min.z) > .5:
            raise RuntimeError('Chair binding failed: expected 19 convex hulls and 100cm height/floor pivot.')
        if len(mesh.get_editor_property('static_materials')) != 2:
            raise RuntimeError('Expected reviewed two-material chair.')
        cube_mesh = u.load_asset('/Engine/BasicShapes/Cube.Cube')
        if cube_mesh is None:
            raise RuntimeError('Engine cube unavailable.')
        report.update({'mesh':mesh.get_path_name(),'convex_hulls':hulls,'binding':binding})
        root = '/Game/EmergencyPOC/Rooms_'+stamp
        if not assets.make_directory(root+'/Maps') or not assets.make_directory(root+'/Materials'):
            raise RuntimeError('Could not create output folders.')
        report['content_root'] = root
        tools = u.AssetToolsHelpers.get_asset_tools()
        def material(name, color):
            mat = tools.create_asset(name,root+'/Materials',u.Material,u.MaterialFactoryNew())
            if mat is None:
                raise RuntimeError('Material creation failed: '+name)
            edit = u.MaterialEditingLibrary
            c = edit.create_material_expression(mat,u.MaterialExpressionConstant3Vector,-300,0)
            c.set_editor_property('constant',u.LinearColor(r=color[0],g=color[1],b=color[2],a=1))
            edit.connect_material_property(c,'',u.MaterialProperty.MP_BASE_COLOR)
            r = edit.create_material_expression(mat,u.MaterialExpressionConstant,-300,180)
            r.set_editor_property('r',.75)
            edit.connect_material_property(r,'',u.MaterialProperty.MP_ROUGHNESS)
            edit.recompile_material(mat)
            if not assets.save_loaded_asset(mat):
                raise RuntimeError('Material save failed.')
            return mat
        mats = {'floor':material('M_RoomFloor',(.12,.17,.20)),
                'wall':material('M_RoomWall',(.5,.57,.61)),
                'aisle':material('M_AisleGuide',(.025,.4,.22)),
                'obstruction':material('M_ObstructionGuide',(.6,.045,.025))}
        physics = tools.create_asset('PM_RoomDemoWood',root+'/Materials',u.PhysicalMaterial,u.PhysicalMaterialFactoryNew())
        physics.set_editor_property('friction',.55)
        physics.set_editor_property('restitution',.05)
        assets.save_loaded_asset(physics)
        def spawn(cls,label,position,rotation=None):
            obj = actors.spawn_actor_from_class(cls,u.Vector(*position),rotation or u.Rotator())
            if obj is None:
                raise RuntimeError('Spawn failed: '+label)
            obj.set_actor_label(label)
            return obj
        def block(label,position,dimensions,kind,collision=True,visible=True):
            obj = spawn(u.StaticMeshActor,label,cm(position))
            component = obj.get_component_by_class(u.StaticMeshComponent)
            if not component.set_static_mesh(cube_mesh):
                raise RuntimeError('Cube assignment failed.')
            # Engine cube is100cm; metre dimensions numerically equal scale factors.
            obj.set_actor_scale3d(u.Vector(*dimensions))
            component.set_material(0,mats[kind])
            component.set_collision_profile_name('BlockAll' if collision else 'NoCollision')
            component.set_visibility(visible,True)
            return obj
        for spec in specs:
            report['stage'] = spec['scene_id']
            level_path = root+'/Maps/L_'+spec['scene_id']+'_'+spec['designated_aisle']['condition']
            if not levels.new_level(level_path):
                raise RuntimeError('Could not create '+level_path)
            w,d,h = (spec['room'][k] for k in ('width_m','depth_m','height_m'))
            gap,dh = spec['room']['door']['width_m'],spec['room']['door']['height_m']
            block('Room floor',(0,d/2,-.1),(w+.3,d+.3,.2),'floor')
            for sign in (-1,1):
                block('Side wall '+str(sign),(sign*(w/2+.075),d/2,h/2),(.15,d,h),'wall')
            block('Front wall - invisible cutaway, collision retained',(0,-.075,h/2),(w,.15,h),'wall',visible=False)
            segment = (w-gap)/2
            for sign in (-1,1):
                block('Exit wall '+str(sign),(sign*(gap/2+segment/2),d+.075,h/2),(segment,.15,h),'wall')
            block('Door lintel',(0,d+.075,dh+(h-dh)/2),(gap,.15,h-dh),'wall')
            aisle = spec['designated_aisle']['bounds_xy_m']
            block('Aisle guide - no collision',(0,(aisle[1]+aisle[3])/2,.003),
                  (aisle[2]-aisle[0],aisle[3]-aisle[1],.004),'aisle',collision=False)
            verified = []
            for item in spec['objects']:
                if item['asset_id'] != 'hunyuan_wooden_chair_8053348':
                    raise RuntimeError('Unsupported chair binding.')
                obj = spawn(u.StaticMeshActor,item['instance_id'],cm(item['position_m']))
                component = obj.get_component_by_class(u.StaticMeshComponent)
                component.set_mobility(u.ComponentMobility.MOVABLE)
                component.set_static_mesh(mesh)
                component.set_world_rotation(u.Rotator(),False,True)
                component.set_world_location(u.Vector(*cm(item['position_m'])),False,True)
                component.set_world_scale3d(u.Vector(1,1,1))
                component.set_collision_profile_name('PhysicsActor')
                component.set_phys_material_override(physics)
                component.set_mass_override_in_kg('None',5.0,True)
                component.set_linear_damping(.05)
                component.set_angular_damping(.1)
                component.set_enable_gravity(True)
                component.set_simulate_physics(True)
                actual = component.get_world_location()
                expected = cm(item['position_m'])
                if max(abs(a-b) for a,b in zip((actual.x,actual.y,actual.z),expected)) > .01 or component.get_up_vector().z < .999:
                    raise RuntimeError('Component transform verification failed: '+item['instance_id'])
                verified.append({'id':item['instance_id'],'location_cm':list(expected)})
                if item['instance_id'] in spec['designated_aisle']['overlapping_instances']:
                    x,y,_ = item['position_m']
                    block('Obstruction guide - no collision',(x,y,.009),(.64,.73,.006),'obstruction',collision=False)
            target = u.Vector(0,400,60)
            for label,position,energy in [('Key',(0,350,700),90000),('Fill',(300,-200,500),45000)]:
                light = spawn(u.RectLight,label+' room light',position,
                               u.MathLibrary.find_look_at_rotation(u.Vector(*position),target))
                lc = light.get_component_by_class(u.RectLightComponent)
                lc.set_mobility(u.ComponentMobility.MOVABLE)
                lc.set_editor_property('intensity_units',u.LightUnits.LUMENS)
                lc.set_intensity(energy)
                lc.set_editor_property('source_width',600.0)
                lc.set_editor_property('source_height',600.0)
                lc.set_editor_property('attenuation_radius',2500.0)
            camera_position = u.Vector(650,-650,1000)
            camera = spawn(u.CameraActor,'Room review camera',(650,-650,1000),
                           u.MathLibrary.find_look_at_rotation(camera_position,u.Vector(0,400,0)))
            camera.get_component_by_class(u.CameraComponent).set_field_of_view(48)
            def caption(label,position,size,camera_position=camera_position):
                pos = u.Vector(*position)
                obj = spawn(u.TextRenderActor,label,position,u.MathLibrary.find_look_at_rotation(pos,camera_position))
                tc = obj.get_component_by_class(u.TextRenderComponent)
                tc.set_text(label)
                tc.set_world_size(size)
                tc.set_horizontal_alignment(u.HorizTextAligment.EHTA_CENTER)
                tc.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
            caption('EXIT',(0,d*100-30,225),35)
            caption(spec['scene_id']+' / '+spec['designated_aisle']['condition'],(0,-80,25),35)
            actors.clear_actor_selection_set()
            if not levels.save_current_level():
                raise RuntimeError('Could not save '+level_path)
            report['maps'].append({'path':level_path,'verified_chairs':verified,'doorway_cm':[gap*100,dh*100],
                  'physics_override':'Chairs enabled as5kg demo rigid bodies at reviewed floor positions; no initial drop.',
                  'front_wall':'Invisible for camera review; collision enabled.'})
        report['stage']='room_setup_complete'
        try:
            levels.pilot_level_actor(camera)
        except (RuntimeError,AttributeError):
            u.log_warning('Maps saved. Select Room review camera and Pilot manually.')
        u.log('ROOM SETUP COMPLETE: '+root+'/Maps')
        u.log('Inspect all three maps. Alt+S enables Chaos; chairs begin on floor, so no large drop is expected.')
    except Exception as exc:
        report.update({'failed_at':report['stage'],'stage':'failed','error':str(exc),'traceback':traceback.format_exc()})
        u.log_error('ROOM SETUP FAILED: '+str(exc))
        raise
    finally:
        path=reports/('room-setup-'+stamp+'.json')
        path.write_text(json.dumps(report,indent=2),encoding='utf-8')
        u.log('Room setup report: '+str(path))


if __name__ == '__main__':
    main()
