"""Protocol test with an explicit fake editor; does not claim Unreal execution."""
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace


def test_bridge_observes_game_world_then_stops_simulation(tmp_path,monkeypatch):
    fake=ModuleType('unreal')
    levels=SimpleNamespace(playing=False,loaded=None)
    levels.is_in_play_in_editor=lambda:levels.playing
    def load(path):
        levels.loaded=path
        return True
    def play():
        levels.playing=True
    def stop():
        levels.playing=False
    levels.load_level=load
    levels.editor_play_simulate=play
    levels.editor_request_end_play=stop
    fake.LevelEditorSubsystem=type('LevelEditorSubsystem',(),{})
    fake.UnrealEditorSubsystem=type('UnrealEditorSubsystem',(),{})
    fake.StaticMeshActor=type('StaticMeshActor',(),{})
    fake.StaticMeshComponent=type('StaticMeshComponent',(),{})
    editor=SimpleNamespace(get_game_world=lambda:object() if levels.playing else None)
    fake.get_editor_subsystem=lambda cls:levels if cls==fake.LevelEditorSubsystem else editor
    positions=iter([0,100])
    component=SimpleNamespace(get_world_location=lambda:SimpleNamespace(x=next(positions),y=0,z=0))
    actor=SimpleNamespace(get_actor_label=lambda:'chair_001',get_component_by_class=lambda cls:component)
    fake.GameplayStatics=SimpleNamespace(get_all_actors_of_class=lambda world,cls:[actor])
    fake.SystemLibrary=SimpleNamespace(get_engine_version=lambda:'5.8.fake_editor')
    fake.Paths=SimpleNamespace(get_project_file_path=lambda:'Fake.uproject')
    fake.EditorLoadingAndSavingUtils=SimpleNamespace(get_dirty_map_packages=list)
    fake.register_slate_post_tick_callback=lambda fn:1
    fake.log=lambda text:None
    fake.log_error=lambda text:None
    monkeypatch.setitem(sys.modules,'unreal',fake)
    path=Path(__file__).resolve().parents[2]/'unreal/scripts/studio_bridge.py'
    spec=importlib.util.spec_from_file_location('bridge_protocol_test',path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.QUEUE=tmp_path
    clock=[100.0]
    module.time=SimpleNamespace(monotonic=lambda:clock[0],time=lambda:clock[0])
    command={'id':'a'*32,'job_id':'b'*32,'action':'simulate','maps':['/Game/EmergencyPOC/Rooms_test/Maps/room_001']}
    (tmp_path/(command['id']+'.command.json')).write_text(json.dumps(command))
    for moment in (100,102,104,116,118):
        clock[0]=moment
        module.bridge.tick(0)
    result=json.loads((tmp_path/(command['id']+'.result.json')).read_text())
    assert result['ok'] is True and levels.playing is False
    assert result['observations'][0]['maximum_endpoint_displacement_m']==1.0
    assert result['observations'][0]['elapsed_seconds']>=10
    assert result['contacts_measured'] is False and result['physics_calibrated'] is False
