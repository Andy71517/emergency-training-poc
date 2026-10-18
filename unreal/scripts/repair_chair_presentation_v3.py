"""Run in Unreal Editor on the existing chair presentation, with simulation stopped."""
import math


def main():
    import unreal as u
    levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    if levels.is_in_play_in_editor():
        raise RuntimeError('Press Esc to stop simulation, then run this script again.')
    all_actors = list(actors.get_all_level_actors())
    cases = [('Display chair', -210, 0, 0), ('Upright drop', 0, 100, 0),
             ('Tilted drop', 210, 120, 30)]
    targets = []
    for label, x, z, roll in cases:
        found = [a for a in all_actors if a.get_actor_label() == label]
        if len(found) != 1:
            raise RuntimeError('Expected exactly one ' + label + '. Open the presentation map first.')
        component = found[0].get_component_by_class(u.StaticMeshComponent)
        if component is None:
            raise RuntimeError('Missing mesh component: ' + label)
        targets.append((label, component, x, z, roll))
    with u.ScopedEditorTransaction('Repair chair presentation component orientations'):
        for label, component, x, z, roll in targets:
            component.modify()
            component.set_simulate_physics(False)
            # Set fields explicitly; do not rely on constructor argument ordering.
            rotation = u.Rotator()
            rotation.set_editor_property('pitch', 0.0)
            rotation.set_editor_property('yaw', 180.0)
            rotation.set_editor_property('roll', float(roll))
            component.set_world_rotation(rotation, False, True)
            component.set_world_location(u.Vector(x, 0, z), False, True)
            component.set_world_scale3d(u.Vector(1, 1, 1))
            if label != 'Display chair':
                component.set_simulate_physics(True)
            up = component.get_up_vector()
            expected = math.cos(math.radians(roll))
            if abs(up.z - expected) > .01:
                raise RuntimeError(f'{label}: orientation check FAILED, up.z={up.z}; expected {expected}. Do not record.')
            u.log(f'CHAIR V3 VERIFIED: {label}: up.z={up.z:.4f}, expected={expected:.4f}')
    actors.clear_actor_selection_set()
    cameras = [a for a in all_actors if a.get_actor_label() == 'Demo camera']
    if len(cameras) == 1:
        levels.pilot_level_actor(cameras[0])
    if not levels.save_current_level():
        raise RuntimeError('Orientation verified, but save failed. Save manually with Ctrl+S.')
    u.log('CHAIR V3 REPAIR COMPLETE. Press G to hide editor icons, inspect, then Alt+S to simulate.')


if __name__ == '__main__':
    main()
