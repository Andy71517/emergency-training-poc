"""Load once with Unreal Tools > Execute Python Script. Loopback workspace only.

Polls fixed file commands from this checkout's logs/studio/engine directory.
Only assemble, simulate and record are supported; prompts and commands never contain code.
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

    def chair_components(self):
        world=self.editor.get_game_world()
        return {actor.get_actor_label():actor.get_component_by_class(u.StaticMeshComponent)
            for actor in u.GameplayStatics.get_all_actors_of_class(world,u.StaticMeshActor)
            if actor.get_actor_label().startswith('chair_')}

    def begin_recording(self):
        task=self.task
        folder=(WORKSPACE/task['job_id']/'captures'/task['id']/f"room_{task['index']+1:03}").resolve()
        if folder.parent.parent.parent.parent!=WORKSPACE.resolve():
            raise RuntimeError('Invalid capture folder.')
        folder.mkdir(parents=True,exist_ok=False)
        cameras=u.GameplayStatics.get_all_actors_of_class(self.editor.get_game_world(),u.CameraActor)
        camera=next((c for c in cameras if c.get_actor_label()=='Room review camera'),None)
        if camera is None:
            raise RuntimeError('Room review camera is missing. Assemble these rooms again before recording.')
        components=self.chair_components()
        # Front-most chair is closest to the review camera. Stable label breaks ties.
        target=min(components,key=lambda label:(components[label].get_world_location().y,label))
        if not components[target].is_simulating_physics():
            raise RuntimeError('The chosen chair is not simulating physics. Reassemble the rooms first.')
        task.update(capture_folder=folder,capture_camera=camera,capture_pending=None,
            capture_frames=[],next_capture=0,capture_error=None,push_target=target,push=None,
            maximum_target_displacement_m=0.0,quiet_since=None,settled=False,
            minimum_target_origin_z_cm=None)

    def capture_frame(self,now,allow_request=True):
        task=self.task
        if task.get('capture_error'):
            return
        elapsed=now-task['started']
        pending=task['capture_pending']
        if pending:
            handle,path,requested=pending
            if handle.is_task_done() and path.is_file():
                task['capture_frames'].append({'file':path.name,'time_seconds':elapsed,
                    'requested_at_seconds':requested})
                task['capture_pending']=None
            elif elapsed-requested>5:
                task['capture_error']='Unreal did not finish saving a requested frame within five seconds.'
                task['capture_pending']=None
        if allow_request and task['capture_pending'] is None and not task['capture_error'] and elapsed>=task['next_capture']:
            index=len(task['capture_frames'])
            if index>=120:
                task['capture_error']='Frame limit reached.'
                return
            path=task['capture_folder']/f'frame_{index:05}.png'
            try:
                handle=u.AutomationLibrary.take_high_res_screenshot(960,540,str(path),
                    camera=task['capture_camera'],delay=0.0,force_game_view=True)
                if handle is None or not handle.is_valid_task():
                    raise RuntimeError('Screenshot task unavailable.')
                task['capture_pending']=(handle,path,elapsed)
                task['next_capture']=elapsed+0.2
            except Exception:  # noqa: BLE001 - preserve physics results if capture fails
                task['capture_error']='Unreal frame capture failed. Check that the room review viewport is available.'

    def observe_push(self,now):
        task=self.task
        elapsed=now-task['started']
        components=self.chair_components()
        component=components[task['push_target']]
        if task['push'] is None and elapsed>=2:
            position=component.get_world_location()
            component.add_velocity_change_impulse_at_location(u.Vector(0,180,0),
                u.Vector(position.x,position.y,position.z+65))
            task['push']={'object_id':task['push_target'],'applied_at_seconds':elapsed,
                'method':'add_velocity_change_impulse_at_location',
                'velocity_change_input_cm_per_s':[0,180,0],
                'application_point_offset_cm':[0,0,65],
                'purpose':'controlled_visual_demo_not_calibrated_force'}
        position=component.get_world_location()
        initial=task['initial'][task['push_target']]
        movement=math.dist(initial,[position.x,position.y,position.z])/100
        task['maximum_target_displacement_m']=max(task['maximum_target_displacement_m'],movement)
        task['minimum_target_origin_z_cm']=min(task['minimum_target_origin_z_cm']
            if task['minimum_target_origin_z_cm'] is not None else position.z,position.z)
        if task['push'] is not None:
            velocity=component.get_physics_linear_velocity()
            angular=component.get_physics_angular_velocity_in_degrees()
            quiet=math.sqrt(velocity.x**2+velocity.y**2+velocity.z**2)<8 and math.sqrt(angular.x**2+angular.y**2+angular.z**2)<8
            task['quiet_since']=(task['quiet_since'] or now) if quiet else None
            task['settled']=bool(task['quiet_since'] is not None and now-task['quiet_since']>=1)

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
            if task['action']=='record':
                cameras=u.GameplayStatics.get_all_actors_of_class(self.editor.get_editor_world(),u.CameraActor)
                camera=next((c for c in cameras if c.get_actor_label()=='Room review camera'),None)
                if camera:
                    self.levels.pilot_level_actor(camera)
            self.levels.editor_play_simulate()
            task.update(phase='starting',deadline=now+30)
        elif state=='starting':
            if self.levels.is_in_play_in_editor() and self.editor.get_game_world() is not None:
                initial=self.sample()
                if not initial:
                    raise RuntimeError('No chair actors found in the simulation world.')
                task.update(phase='running',started=now,initial=initial,deadline=now+10)
                if task['action']=='record':
                    self.begin_recording()
            elif now>task['deadline']:
                raise RuntimeError('Unreal did not enter simulation within 30 seconds.')
        elif state=='running':
            if not self.levels.is_in_play_in_editor():
                raise RuntimeError('Simulation was stopped before observation completed.')
            if task['action']=='record':
                self.capture_frame(now,allow_request=now<task['deadline'])
                self.observe_push(now)
                if now>=task['deadline'] and task['capture_pending'] is not None and now<task['deadline']+5:
                    return
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
                if task['action']=='record':
                    observation=task['observations'][-1]
                    observation.update(controlled_input=task['push'],target_maximum_displacement_m=task['maximum_target_displacement_m'],
                        target_settled_at_end=task['settled'],minimum_target_origin_z_cm=task['minimum_target_origin_z_cm'],
                        motion_check_passed=task['maximum_target_displacement_m']>=0.05,
                        settling_thresholds={'linear_cm_per_s':8,'angular_degrees_per_s':8,'quiet_seconds':1})
                    capture={'stage':'unreal_viewport_frames','map':observation['map'],
                        'scene_id':f"room_{task['index']+1:03}",'frames':task['capture_frames'],
                        'duration_seconds':now-task['started'],'target_capture_fps':5,
                        'camera_label':'Room review camera','resolution_px':[960,540],
                        'timing':'approximate_wall_clock_at_frame_completion','capture_error':task['capture_error']}
                    atomic(task['capture_folder']/'capture.json',capture)
                    observation['capture']={'scene_id':capture['scene_id'],'frame_count':len(capture['frames']),
                        'error':capture['capture_error']}
                self.levels.editor_request_end_play()
                task.update(phase='stopping',deadline=now+30)
        elif state=='stopping':
            if not self.levels.is_in_play_in_editor():
                task['index']+=1
                if task['index']==len(task['maps']):
                    self.finish({'ok':True,'action':task['action'],'job_id':task['job_id'],'run':task['id'],
                        'observations':task['observations'],'engine_version':u.SystemLibrary.get_engine_version(),
                        'physics_calibrated':False,'contacts_measured':False})
                else:
                    task['phase']='load'
            elif now>task['deadline']:
                raise RuntimeError('Unreal did not leave simulation within 30 seconds.')

    def tick(self,delta):
        now=time.monotonic()
        try:
            if self.task and self.task.get('action') in ('simulate','record'):
                self.advance_simulation()
            if now-self.last_poll<1:
                return
            self.last_poll=now
            atomic(QUEUE/'heartbeat.json',{'time':time.time(),'engine_version':u.SystemLibrary.get_engine_version(),
                'activity':{'job_id':self.task['job_id'],'action':self.task['action'],
                    'room':self.task.get('index',0)+1,'total':len(self.task.get('maps',[]))} if self.task else None,
                'busy':self.task is not None,'capabilities':['assemble','simulate','record'],'bridge_version':2,'project':Path(u.Paths.get_project_file_path()).name})
            if self.task:
                return
            paths=sorted(QUEUE.glob('*.command.json'))
            if not paths:
                return
            path=paths[0]
            task=json.loads(path.read_text(encoding='utf-8'))
            path.rename(path.with_suffix('.claimed'))
            if task.get('action') not in ('assemble','simulate','record') or len(task.get('job_id',''))!=32:
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
                if self.task.get('action') in ('simulate','record') and self.levels.is_in_play_in_editor():
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
if previous is not None:
    bridge.mesh_path=previous.mesh_path
bridge.handle=u.register_slate_post_tick_callback(bridge.tick)
u._fieldwork_bridge=bridge
u.log('FIELDWORK bridge connected to '+str(WORKSPACE))
