"""Explicit fake-editor recording protocol; actual Unreal capture needs user verification."""
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

from backend.tests.test_studio_video import write_png


def test_recording_pushes_once_saves_frames_and_stops(tmp_path,monkeypatch):
    fake=ModuleType('unreal')
    levels=SimpleNamespace(playing=False)
    levels.is_in_play_in_editor=lambda:levels.playing
    levels.load_level=lambda path:True
    levels.pilot_level_actor=lambda actor:None
    def play():
        levels.playing=True
    def stop():
        levels.playing=False
    levels.editor_play_simulate=play
    levels.editor_request_end_play=stop
    for name in ('LevelEditorSubsystem','UnrealEditorSubsystem','StaticMeshActor','StaticMeshComponent','CameraActor'):
        setattr(fake,name,type(name,(),{}))
    world=object()
    editor=SimpleNamespace(get_game_world=lambda:world if levels.playing else None,get_editor_world=lambda:world)
    fake.get_editor_subsystem=lambda cls:levels if cls==fake.LevelEditorSubsystem else editor
    position=[0.,0.,0.]
    pushes=[]
    def push(vector,point):
        pushes.append((vector,point))
        position[1]=75.
    zero=lambda:SimpleNamespace(x=0.,y=0.,z=0.)
    component=SimpleNamespace(get_world_location=lambda:SimpleNamespace(x=position[0],y=position[1],z=position[2]),
        is_simulating_physics=lambda:True,add_velocity_change_impulse_at_location=push,
        get_physics_linear_velocity=zero,get_physics_angular_velocity_in_degrees=zero)
    actor=SimpleNamespace(get_actor_label=lambda:'chair_001',get_component_by_class=lambda cls:component)
    camera=SimpleNamespace(get_actor_label=lambda:'Room review camera')
    fake.GameplayStatics=SimpleNamespace(get_all_actors_of_class=lambda w,cls:[camera] if cls==fake.CameraActor else [actor])
    fake.Vector=lambda x,y,z:SimpleNamespace(x=x,y=y,z=z)
    screenshots=[]
    def screenshot(width,height,filename,**kwargs):
        assert (width,height)==(960,540) and kwargs['camera'] is camera and kwargs['force_game_view'] is True
        screenshots.append(filename)
        write_png(Path(filename),(50,int(position[1])+50,90))
        return SimpleNamespace(is_valid_task=lambda:True,is_task_done=lambda:True)
    fake.AutomationLibrary=SimpleNamespace(take_high_res_screenshot=screenshot)
    fake.SystemLibrary=SimpleNamespace(get_engine_version=lambda:'5.8.fake_editor')
    fake.Paths=SimpleNamespace(get_project_file_path=lambda:'Fake.uproject')
    fake.EditorLoadingAndSavingUtils=SimpleNamespace(get_dirty_map_packages=list)
    fake.register_slate_post_tick_callback=lambda fn:1
    fake.log=lambda text:None
    errors=[]
    fake.log_error=errors.append
    monkeypatch.setitem(sys.modules,'unreal',fake)
    path=Path(__file__).resolve().parents[2]/'unreal/scripts/studio_bridge.py'
    spec=importlib.util.spec_from_file_location('recording_protocol_test',path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.WORKSPACE=tmp_path/'work';module.QUEUE=module.WORKSPACE/'engine';module.QUEUE.mkdir(parents=True)
    clock=[100.0]
    module.time=SimpleNamespace(monotonic=lambda:clock[0],time=lambda:clock[0])
    command={'id':'a'*32,'job_id':'b'*32,'action':'record','maps':['/Game/EmergencyPOC/Rooms_test/Maps/room_001']}
    (module.QUEUE/(command['id']+'.command.json')).write_text(json.dumps(command))
    result_path=module.QUEUE/(command['id']+'.result.json')
    for i in range(150):
        clock[0]=100+i*.1
        module.bridge.tick(.1)
        if result_path.is_file():break
    result=json.loads(result_path.read_text())
    assert result['ok'] is True and not levels.playing and not errors
    assert len(pushes)==1 and pushes[0][0].y==180 and pushes[0][1].z==65
    observation=result['observations'][0]
    assert observation['target_maximum_displacement_m']==.75 and observation['motion_check_passed'] is True
    assert observation['target_settled_at_end'] is True
    capture=json.loads((module.WORKSPACE/command['job_id']/'captures'/command['id']/'room_001/capture.json').read_text())
    assert len(capture['frames'])>10 and len(screenshots)==len(capture['frames'])
    assert capture['capture_error'] is None and result['contacts_measured'] is False
