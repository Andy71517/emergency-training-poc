"""Load once with Unreal Tools > Execute Python Script. Loopback workspace only.

Polls fixed file commands from this checkout's logs/studio/engine directory.
Only assemble and simulate are supported; prompts and commands never contain code.
"""
import importlib.util
import json
import math
import time
from pathlib import Path

import unreal as u

ROOT=Path(__file__).resolve().parents[2]
WORKSPACE=ROOT/'logs'/'studio'
QUEUE=WORKSPACE/'engine'
QUEUE.mkdir(parents=True,exist_ok=True)


def atomic(path,data):
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(data,indent=2,allow_nan=False),encoding='utf-8')
    temp.replace(path)


class Bridge:
    def __init__(self):
        self.last_poll=0
        self.task=None
        self.mesh_path=None
        self.levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
        self.editor=u.get_editor_subsystem(u.UnrealEditorSubsystem)

    def finish(self,result):
        atomic(QUEUE/(self.task['id']+'.result.json'),result)
        self.task=None

    def sample(self):
        world=self.editor.get_game_world()
        if world is None:
            return {}
        result={}
        for actor in u.GameplayStatics.get_all_actors_of_class(world,u.StaticMeshActor):
            label=actor.get_actor_label()
            if not label.startswith('chair_'):
                continue
            component=actor.get_component_by_class(u.StaticMeshComponent)
            p=component.get_world_location()
            if not all(math.isfinite(v) for v in (p.x,p.y,p.z)):
                raise RuntimeError('Non-finite chair transform during simulation.')
            result[label]=[p.x,p.y,p.z]
        return result

    def advance_simulation(self):
        task=self.task
        now=time.monotonic()
        state=task['phase']
        if state=='load':
            if self.levels.is_in_play_in_editor():
                raise RuntimeError('Stop your current simulation before requesting a run.')
            if u.EditorLoadingAndSavingUtils.get_dirty_map_packages():
                raise RuntimeError('Save your current level before running the batch.')
            if not self.levels.load_level(task['maps'][task['index']]):
                raise RuntimeError('Could not load a generated room map.')
            self.levels.editor_play_simulate()
            task.update(phase='starting',deadline=now+30)
        elif state=='starting':
            if self.levels.is_in_play_in_editor() and self.editor.get_game_world() is not None:
                initial=self.sample()
                if not initial:
                    raise RuntimeError('No chair actors found in the simulation world.')
                task.update(phase='running',started=now,initial=initial,deadline=now+10)
            elif now>task['deadline']:
                raise RuntimeError('Unreal did not enter simulation within 30 seconds.')
        elif state=='running':
            if not self.levels.is_in_play_in_editor():
                raise RuntimeError('Simulation was stopped before observation completed.')
            if now>=task['deadline']:
                final=self.sample()
                if set(final)!=set(task['initial']):
                    raise RuntimeError('Chair actor count changed during simulation.')
                displacement={label:math.dist(task['initial'][label],final[label])/100 for label in final}
                task['observations'].append({'map':task['maps'][task['index']],
                    'elapsed_seconds':now-task['started'],'chairs_observed':len(final),
                    'initial_positions_cm':task['initial'],'final_positions_cm':final,
                    'maximum_endpoint_displacement_m':max(displacement.values(),default=0),
                    'contacts_measured':False,'physics_calibrated':False})
                self.levels.editor_request_end_play()
                task.update(phase='stopping',deadline=now+30)
        elif state=='stopping':
            if not self.levels.is_in_play_in_editor():
                task['index']+=1
                if task['index']==len(task['maps']):
                    self.finish({'ok':True,'action':'simulate','job_id':task['job_id'],
                        'observations':task['observations'],'engine_version':u.SystemLibrary.get_engine_version(),
                        'physics_calibrated':False,'contacts_measured':False})
                else:
                    task['phase']='load'
            elif now>task['deadline']:
                raise RuntimeError('Unreal did not leave simulation within 30 seconds.')

    def tick(self,delta):
        now=time.monotonic()
        try:
            if self.task and self.task.get('action')=='simulate':
                self.advance_simulation()
            if now-self.last_poll<1:
                return
            self.last_poll=now
            atomic(QUEUE/'heartbeat.json',{'time':time.time(),'engine_version':u.SystemLibrary.get_engine_version(),
                'busy':self.task is not None,'project':Path(u.Paths.get_project_file_path()).name})
            if self.task:
                return
            paths=sorted(QUEUE.glob('*.command.json'))
            if not paths:
                return
            path=paths[0]
            task=json.loads(path.read_text(encoding='utf-8'))
            path.rename(path.with_suffix('.claimed'))
            if task.get('action') not in ('assemble','simulate') or len(task.get('job_id',''))!=32:
                raise RuntimeError('Invalid fixed-action workspace command.')
            self.task=task
            if task['action']=='assemble':
                package=(WORKSPACE/task['job_id']).resolve()
                if package.parent!=WORKSPACE.resolve():
                    raise RuntimeError('Package must belong to the local workspace.')
                module_path=ROOT/'unreal/scripts/assemble_unreal58_rooms.py'
                spec=importlib.util.spec_from_file_location('fieldwork_room_assembler',module_path)
                module=importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                report=module.main(package,self.mesh_path)
                self.mesh_path=report['mesh']
                self.finish({'ok':True,'action':'assemble','job_id':task['job_id'],'report':report})
            else:
                if not task.get('maps') or any(not p.startswith('/Game/EmergencyPOC/Rooms_') for p in task['maps']):
                    raise RuntimeError('Simulation is restricted to generated FIELDWORK maps.')
                task.update(phase='load',index=0,observations=[])
        except Exception as exc:  # noqa: BLE001 - return editor failures to the local workspace
            u.log_error('FIELDWORK: '+str(exc))
            if self.task:
                if self.task.get('action')=='simulate' and self.levels.is_in_play_in_editor():
                    self.levels.editor_request_end_play()
                self.finish({'ok':False,'action':self.task['action'],'job_id':self.task['job_id'],
                    'message':str(exc)[:800]})


previous=getattr(u,'_fieldwork_bridge',None)
if previous is not None:
    if previous.task:
        raise RuntimeError('The previous bridge has an active task. Wait for it to finish.')
    u.unregister_slate_post_tick_callback(previous.handle)
if not u.SystemLibrary.get_engine_version().startswith('5.8.'):
    raise RuntimeError('This bridge targets Unreal 5.8.x.')
bridge=Bridge()
bridge.handle=u.register_slate_post_tick_callback(bridge.tick)
u._fieldwork_bridge=bridge
u.log('FIELDWORK bridge connected to '+str(WORKSPACE))
