"""Run in Unreal 5.8 with the verified L_ChairVisualDemo open and simulation stopped.
Creates a separate presentation level using existing assets; no downloads or reimports.
Keep setup_unreal58_chair_demo.py beside this script.
"""
import hashlib
import json
import runpy
import traceback
import uuid
from datetime import UTC, datetime
from pathlib import Path

HELPER_SHA256 = "7127b3e42929af8b49eaff766279b10e12d925ac96fa9ba475728db0a92e7394"
EXPECTED_LABELS = ('Display chair', 'Upright drop', 'Tilted drop', 'Demo floor', 'Demo camera')


def load_helper(folder):
    path = Path(folder) / 'setup_unreal58_chair_demo.py'
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != HELPER_SHA256:
        raise RuntimeError('Extract both supplied Python files together; helper is missing or changed.')
    return runpy.run_path(str(path), run_name='chair_setup_helpers')


def main():
    import unreal as u

    stamp = datetime.now(UTC).strftime('%Y%m%d_%H%M%S') + '_' + uuid.uuid4().hex[:6]
    reports = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_saved_dir())) / 'EmergencyPOC'
    reports.mkdir(parents=True, exist_ok=True)
    report_path = reports / ('chair-presentation-' + stamp + '.json')
    report = {'stage': 'preflight', 'engine_version': u.SystemLibrary.get_engine_version(),
              'simulation_started_by_script': False, 'presentation_reviewed': False,
              'prior_drop_observation': 'Andy reported both raised chairs fell and settled within 1-2 seconds on 2026-10-18.',
              'physics_calibrated': False}
    try:
        if not report['engine_version'].startswith('5.8.'):
            raise RuntimeError('This script targets Unreal Engine 5.8.x.')
        helper = load_helper(Path(__file__).resolve().parent)
        levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
        actors = u.get_editor_subsystem(u.EditorActorSubsystem)
        assets = u.get_editor_subsystem(u.EditorAssetSubsystem)
        if levels.is_in_play_in_editor():
            raise RuntimeError('Press Esc to stop simulation, then rerun.')
        if u.EditorLoadingAndSavingUtils.get_dirty_map_packages():
            raise RuntimeError('Save the current level with Ctrl+S, then rerun.')
        current = list(actors.get_all_level_actors())
        matched = {}
        for label in EXPECTED_LABELS:
            matches = [a for a in current if a.get_actor_label() == label]
            if len(matches) != 1:
                raise RuntimeError('Open the original chair demo level; expected exactly one actor: ' + label)
            matched[label] = matches[0]
        if any(a.get_actor_label().startswith('POC caption:') for a in current):
            raise RuntimeError('Presentation already open. Reuse it, or open the original demo before creating another.')
        world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
        report['baseline_world'] = world.get_path_name()
        mesh = matched['Display chair'].get_component_by_class(u.StaticMeshComponent).get_editor_property('static_mesh')
        if mesh is None:
            raise RuntimeError('Display chair has no static mesh.')
        for label in ('Upright drop', 'Tilted drop'):
            other = matched[label].get_component_by_class(u.StaticMeshComponent)
            if other.get_editor_property('static_mesh') != mesh:
                raise RuntimeError('All three cases must use the same reviewed chair mesh.')
        hulls = u.get_editor_subsystem(u.StaticMeshEditorSubsystem).get_convex_collision_count(mesh)
        if hulls != 19:
            raise RuntimeError(f'Expected 19 convex hulls; got {hulls}.')
        floor_component = matched['Demo floor'].get_component_by_class(u.StaticMeshComponent)
        floor_material = floor_component.get_material(0)
        physics = floor_component.get_editor_property('body_instance').get_editor_property('phys_material_override')
        if floor_material is None or physics is None:
            raise RuntimeError('Original floor material or physical material is missing.')
        root = '/Game/EmergencyPOC/ChairPresentation_' + stamp
        if assets.does_directory_exist(root):
            raise RuntimeError('Presentation destination already exists.')
        if not assets.make_directory(root + '/Maps'):
            raise RuntimeError('Could not create the separate presentation folder.')
        report.update({'stage': 'create_presentation', 'created_content_root': root,
                       'mesh_asset': mesh.get_path_name(), 'convex_collision_count': hulls})
        level_path, _ = helper['build_scene'](u, actors, levels, root, mesh, floor_material, physics)
        report['level_asset'] = level_path
        scene = {a.get_actor_label(): a for a in actors.get_all_level_actors()}
        # A level-local layout. Shared meshes, materials, and the original map are untouched.
        cases = [('Display chair', (-210, 0, 0), u.Rotator(pitch=0, yaw=180, roll=0)),
                 ('Upright drop', (0, 0, 100), u.Rotator(pitch=0, yaw=180, roll=0)),
                 ('Tilted drop', (210, 0, 120), u.Rotator(pitch=0, yaw=180, roll=30))]
        for label, position, rotation in cases:
            actor = scene[label]
            component = actor.get_component_by_class(u.StaticMeshComponent)
            dynamic = label != 'Display chair'
            component.set_simulate_physics(False)
            actor.set_actor_location_and_rotation(u.Vector(*position), rotation, False, True)
            if dynamic:
                component.set_simulate_physics(True)
        camera = scene['Demo camera']
        camera_position = u.Vector(0, -1100, 400)
        camera.set_actor_location_and_rotation(camera_position,
            u.MathLibrary.find_look_at_rotation(camera_position, u.Vector(0, 0, 115)), False, True)
        camera.get_component_by_class(u.CameraComponent).set_field_of_view(48)
        # TextRender's positive X normal faces the camera; labels stay fixed during the drop.
        def caption(text, position, size, color):
            rotation = u.MathLibrary.find_look_at_rotation(u.Vector(*position), camera_position)
            actor = helper['spawn'](u, actors, u.TextRenderActor, 'POC caption: ' + text, position, rotation)
            component = actor.get_component_by_class(u.TextRenderComponent)
            component.set_text(text)
            component.set_world_size(size)
            component.set_horizontal_alignment(u.HorizTextAligment.EHTA_CENTER)
            component.set_text_render_color(u.Color(r=color[0], g=color[1], b=color[2], a=255))
            component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
            component.set_editor_property('cast_shadow', False)
        caption('GENERATED ASSET / PHYSICS DEMO', (0, 30, 295), 18, (235, 241, 255))
        caption('VT ARC Hunyuan  >  Blender  >  Unreal Chaos', (0, 30, 265), 11, (165, 205, 235))
        for x, heading, detail in [(-210, 'REFERENCE', 'Stationary'),
                                    (0, 'UPRIGHT DROP', 'Gravity + floor contact'),
                                    (210, 'TILTED DROP', '30-degree initial tilt')]:
            caption(heading, (x, -135, 9), 12, (235, 241, 255))
            caption(detail, (x, -185, 8), 8, (165, 205, 235))
        caption('Proof of concept | Demo mass / friction | Normal-speed simulation',
                (0, -290, 6), 8, (190, 200, 215))
        actors.clear_actor_selection_set()
        if not levels.save_current_level():
            raise RuntimeError('Could not save the finished presentation level.')
        try:
            levels.pilot_level_actor(camera)
        except (AttributeError, RuntimeError) as exc:
            u.log_warning('Presentation saved. Pilot Demo camera manually: ' + str(exc))
        report.update({'stage': 'presentation_complete', 'time_scale': 1.0,
                       'case_initial_transforms': [{'label': c[0], 'location_cm': list(c[1]),
                                                   'yaw_degrees': 180, 'roll_degrees': 30 if c[0] == 'Tilted drop' else 0}
                                                  for c in cases],
                       'assumptions': {'dynamic_mass_kg': 5, 'friction': .55, 'restitution': .05,
                                       'dimensions_measured_from_real_chair': False},
                       'capture': 'G to hide icons; start screen recording; hold initial view 3 seconds; Alt+S; wait 8 seconds; stop recording; Esc resets.'})
        u.log('CHAIR PRESENTATION READY: ' + level_path)
        u.log('Inspect once, then record: 3 seconds before Alt+S, 8 seconds after. Esc resets the saved initial transforms.')
    except Exception as exc:
        report.update({'failed_at': report['stage'], 'stage': 'failed',
                       'error': str(exc), 'traceback': traceback.format_exc()})
        u.log_error('CHAIR PRESENTATION FAILED: ' + str(exc))
        raise
    finally:
        report_path.write_text(json.dumps(report, indent=2), encoding='utf-8')
        u.log('Presentation report: ' + str(report_path))


if __name__ == '__main__':
    main()
