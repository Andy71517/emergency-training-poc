"""Engine-independent setup regression checks; these do not run Chaos."""

import runpy
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / 'unreal/scripts'


@dataclass
class Rotator:
    # Unreal Python's positional constructor order differs from FRotator in C++.
    roll: float = 0
    pitch: float = 0
    yaw: float = 0


def test_demo_spawns_an_actual_tilt_and_keeps_reference_static():
    helper = runpy.run_path(str(SCRIPTS / 'setup_unreal58_chair_demo.py'))
    spawned = []

    def spawn(_cls, location, rotation):
        actor = Mock()
        spawned.append((actor, location, rotation))
        return actor

    engine = SimpleNamespace(
        Vector=lambda x, y, z: SimpleNamespace(x=x, y=y, z=z), Rotator=Rotator,
        StaticMeshActor=object(), StaticMeshComponent=object(),
        RectLight=object(), RectLightComponent=object(), CameraActor=object(),
        CameraComponent=object(), ComponentMobility=SimpleNamespace(MOVABLE=1),
        LightUnits=SimpleNamespace(LUMENS=1), load_asset=Mock(return_value=object()),
        MathLibrary=SimpleNamespace(find_look_at_rotation=Mock(return_value=Rotator())),
    )
    actors = SimpleNamespace(spawn_actor_from_class=spawn)
    levels = Mock()
    path, cases = helper['build_scene'](
        engine, actors, levels, '/Game/Test', object(), object(), object(),
    )
    by_label = {a.set_actor_label.call_args.args[0]: (a, p, r) for a, p, r in spawned}
    tilted, location, rotation = by_label['Tilted drop']
    assert rotation == Rotator(roll=30, pitch=0, yaw=0)
    assert location.z == 85
    tilted.get_component_by_class.return_value.set_simulate_physics.assert_called_once_with(True)
    reference = by_label['Display chair'][0].get_component_by_class.return_value
    reference.set_simulate_physics.assert_not_called()
    assert [c['simulate_physics'] for c in cases] == [False, True, True]
    assert path == '/Game/Test/Maps/L_ChairVisualDemo'
    levels.save_current_level.assert_called_once()


def test_presentation_accepts_current_helper_and_rejects_changed_copy(tmp_path):
    presentation = runpy.run_path(str(SCRIPTS / 'prepare_unreal58_chair_presentation.py'))
    assert callable(presentation['load_helper'](SCRIPTS)['build_scene'])
    helper = tmp_path / 'setup_unreal58_chair_demo.py'
    helper.write_bytes((SCRIPTS / helper.name).read_bytes() + b'\n# altered\n')
    with pytest.raises(RuntimeError, match='missing or changed'):
        presentation['load_helper'](tmp_path)
    helper.unlink()
    with pytest.raises(RuntimeError, match='missing or changed'):
        presentation['load_helper'](tmp_path)
