"""Local application workers and portable, hash-bound engine handoffs."""
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
import uuid
import zipfile
from pathlib import Path

from arc.scripts.check_scenario_planner_access import safe_error_detail
from backend.app.studio.service import REPO, local_settings, settings


def connection_check():
    token, model = settings()
    if not token:
        raise ValueError('Set ARC_LLM_API_KEY in backend/.env first.')
    request = urllib.request.Request('https://llm-api.arc.vt.edu/api/v1/chat/completions',
        data=json.dumps({'model':model, 'max_tokens':256,
            'messages':[{'role':'user','content':'Reply with ARC access OK.'}]}).encode(),
        headers={'Authorization':'Bearer '+token.strip(),'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(request,timeout=45) as response:
            data=json.loads(response.read(1_000_000))
        message=data['choices'][0]['message']
        if not (message.get('content') or message.get('reasoning_content')):
            raise ValueError('ARC responded without model text. Try again later.')
    except urllib.error.HTTPError as exc:
        raise ValueError(f'ARC HTTP {exc.code}: '+safe_error_detail(exc.read(16384),token)) from None
    except (urllib.error.URLError, TimeoutError):
        raise ValueError('Cannot reach ARC. Check the VT VPN, internet access and service availability.') from None
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        raise ValueError('ARC returned an unexpected response format.') from None
    return {'ok':True,'message':'Authenticated model response received.','model':model}


class Pipeline:
    def __init__(self, service):
        self.service=service
        # A local application crash is not evidence of completion.
        for job in service.list():
            changed=False
            for stage in job.get('pipeline',{}).values():
                if stage.get('status') in ('queued','running'):
                    command_id=stage.get('command_id')
                    if command_id:
                        pending=service.directory/'engine'/(command_id+'.command.json')
                        if pending.is_file():
                            pending.rename(pending.with_suffix('.cancelled'))
                    stage.update(status='interrupted',message='Backend restarted; rerun this stage.')
                    changed=True
            if changed:
                service.save(job)

    def config(self):
        values=local_settings()
        exe,chair=(Path(values[k]) if values[k] else None for k in ('BLENDER_EXECUTABLE','CHAIR_BLEND'))
        engine=self.engine_status()
        return {'blender_ready':bool(exe and exe.is_file() and chair and chair.is_file()),
                'blender_executable_set':bool(exe and exe.is_file()),
                'chair_bound':bool(chair and chair.is_file()),
                'asset_id':'hunyuan_wooden_chair_8053348',
                'asset_label':'Reviewed wooden chair · 1 m assumed height',
                'unreal_mode':'local_editor_bridge','engine':engine,
                'requirements':['BLENDER_EXECUTABLE: full path to Blender 5.1 executable',
                    'CHAIR_BLEND: full path to chair-collision-complete.blend'],
                'new_asset_generation':'ARC GPU jobs remain separate from this local worker.'}

    def engine_status(self):
        try:
            data=json.loads((self.service.directory/'engine/heartbeat.json').read_text(encoding='utf-8'))
            return {'connected':time.time()-data['time']<15,'busy':bool(data['busy']),
                    'version':data.get('engine_version',''),'project':data.get('project','')}
        except (OSError,ValueError,KeyError,TypeError):
            return {'connected':False,'busy':False}

    def binding(self, job):
        folder=self.service.directory/job['id']
        manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
        return {'job_id':job['id'],'rooms':[{'file':s['scene_id']+'.json',
                'sha256':manifest['files_sha256'][s['scene_id']+'.json']} for s in job['scenes']],
                'review_status':'spatial_draft_requires_visual_review',
                'physics_calibrated':False,'binary_assets_included':False}

    def enqueue_engine(self,job_id,action):
        if action not in ('assemble','simulate'):
            raise ValueError('Unsupported editor action.')
        engine=self.engine_status()
        if engine['busy']:
            raise ValueError('The Unreal bridge is busy. Wait for its current action to finish.')
        if not engine['connected']:
            raise ValueError('Load unreal/scripts/studio_bridge.py once in your Unreal 5.8 editor. See Connections.')
        with self.service.lock:
            job=self.ready(job_id)
            if any(s.get('status') in ('queued','running') for j in self.service.list()
                   for name,s in j.get('pipeline',{}).items() if name in ('unreal','simulation')):
                raise ValueError('An Unreal action is already active. Wait for it to finish.')
            maps=job.get('pipeline',{}).get('unreal',{}).get('maps',[])
            if action=='simulate' and not maps:
                raise ValueError('Assemble this batch in Unreal before requesting Chaos playback.')
            if action=='simulate' and any(not p.startswith('/Game/EmergencyPOC/Rooms_') for p in maps):
                raise ValueError('Automatic playback is restricted to generated FIELDWORK maps.')
            folder=self.service.directory/job_id
            (folder/'room-package.json').write_text(json.dumps(self.binding(job),indent=2),encoding='utf-8')
            queue=self.service.directory/'engine'
            queue.mkdir(exist_ok=True)
            command={'id':uuid.uuid4().hex,'job_id':job_id,'action':action,'maps':maps}
            path=queue/(command['id']+'.command.json')
            temp=path.with_suffix('.tmp')
            temp.write_text(json.dumps(command),encoding='utf-8')
            temp.replace(path)
            name='unreal' if action=='assemble' else 'simulation'
            job.setdefault('pipeline',{})[name]={'status':'queued','command_id':command['id'],
                'message':'Waiting for the Unreal editor bridge. Keep the editor open.'}
            self.service.save(job)
        return job

    def sync_engine(self):
        queue=self.service.directory/'engine'
        for job in self.service.list():
            for name in ('unreal','simulation'):
                state=job.get('pipeline',{}).get(name,{})
                if state.get('status')=='queued' and (queue/(state['command_id']+'.command.claimed')).is_file():
                    state=dict(state,status='running',message='Unreal is assembling room maps.' if name=='unreal'
                        else 'Unreal is observing each map for ten seconds. Watch the editor for playback.')
                    self.update(job['id'],name,state)
        for path in queue.glob('*.result.json'):
            matched=None
            try:
                result=json.loads(path.read_text(encoding='utf-8'))
                job=self.service.get(result['job_id'])
                name='unreal' if result['action']=='assemble' else 'simulation'
                state=job.get('pipeline',{}).get(name,{})
                if state.get('command_id')!=path.name.split('.')[0] or state.get('status') not in ('queued','running'):
                    continue
                matched=(job['id'],name)
                if not result.get('ok'):
                    token,_=settings()
                    message=safe_error_detail(json.dumps({'message':result.get('message','Editor action failed.')}).encode(),token)
                    self.update(job['id'],name,{'status':'failed','message':message})
                elif name=='unreal':
                    self.import_unreal_report(job['id'],result['report'],'local_editor_bridge')
                else:
                    observations=result.get('observations',[])
                    if len(observations)!=len(job['scenes']):
                        raise ValueError('Incomplete engine observation report.')
                    allowed_maps=set(job['pipeline']['unreal']['maps'])
                    if {o.get('map') for o in observations}!=allowed_maps:
                        raise ValueError('Simulation report does not match assembled maps.')
                    (self.service.directory/job['id']/'chaos-report.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
                    self.update(job['id'],'simulation',{'status':'playback_reported',
                        'message':'Editor reported timed Chaos playback for every map. Contacts and calibration are not validated.',
                        'room_count':len(observations),'evidence':'local_editor_bridge',
                        'maximum_endpoint_displacement_m':max(o['maximum_endpoint_displacement_m'] for o in observations),
                        'physics_calibrated':False,'contacts_measured':False})
            except (OSError,ValueError,KeyError,TypeError):
                # Keep malformed output for inspection, but release the failed action.
                if matched:
                    self.update(*matched,{'status':'failed','message':'Editor report was incomplete or did not match the batch. Review the editor log, then rerun.'})
                continue

    def ready(self, job_id):
        job=self.service.get(job_id)
        if job['status']!='review_ready':
            raise ValueError('Generate a valid layout batch before running this stage.')
        return job

    def update(self, job_id, name, value):
        with self.service.lock:
            job=self.service.get(job_id)
            job.setdefault('pipeline',{})[name]=value
            self.service.save(job)

    def blender(self, job_id):
        if not self.config()['blender_ready']:
            raise ValueError('Set BLENDER_EXECUTABLE and CHAIR_BLEND in backend/.env. Open Connections for instructions.')
        with self.service.lock:
            job=self.ready(job_id)
            if job.get('pipeline',{}).get('blender',{}).get('status') in ('queued','running'):
                raise ValueError('Blender is already running for this batch.')
            run=uuid.uuid4().hex
            job.setdefault('pipeline',{})['blender']={'status':'queued','run':run,'message':'Waiting for the local worker.'}
            self.service.save(job)
            self.service.pool.submit(self.run_blender,job_id,run)
        return self.service.get(job_id)

    def run_blender(self, job_id, run):
        output=self.service.directory/job_id/'blender'/run
        output.mkdir(parents=True)
        self.update(job_id,'blender',{'status':'running','run':run,'message':'Assembling reviewed assets and rendering a preview.'})
        try:
            values=local_settings()
            args=[values['BLENDER_EXECUTABLE'],'--background','--factory-startup',
                  '--python-exit-code','1','--python',str(REPO/'scripts/blender/studio_worker.py'),'--',
                  str(self.service.directory/job_id), values['CHAIR_BLEND'], str(output)]
            # Strip the private planner key from child process environments.
            env={k:v for k,v in os.environ.items() if k!='ARC_LLM_API_KEY'}
            result=subprocess.run(args,cwd=REPO,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=1800,check=False)
            # Full process output is deliberately not returned to the browser or saved.
            if result.returncode or not all((output/n).is_file() for n in ('rooms.blend','preview.png','report.json')):
                raise ValueError('Blender did not produce a complete batch. Check Blender 5.1 and the prepared chair binding, then rerun.')
            report=json.loads((output/'report.json').read_text(encoding='utf-8'))
            if report.get('scene_count') != len(self.ready(job_id)['scenes']):
                raise ValueError('Blender returned an unexpected room count.')
            self.update(job_id,'blender',{'status':'complete','run':run,
                'message':'Room assembly and preview completed. Inspect the Blender file before engine handoff.',
                'report':report})
        except subprocess.TimeoutExpired:
            self.update(job_id,'blender',{'status':'failed','run':run,'message':'Blender exceeded the 30-minute worker limit.'})
        except Exception:  # noqa: BLE001 - persist sanitized worker boundary failures
            self.update(job_id,'blender',{'status':'failed','run':run,
                'message':'Blender could not complete assembly. Verify Blender 5.1 and the prepared chair file in Connections.'})

    def bundle(self, job_id, target):
        job=self.ready(job_id)
        folder=self.service.directory/job_id
        run=uuid.uuid4().hex
        destination=folder/f'{target}-{run}.zip'
        manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
        binding=self.binding(job)
        with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as archive:
            for name in ['manifest.json',*manifest['files_sha256']]:
                archive.write(folder/name,name)
            archive.writestr('room-package.json',json.dumps(binding,indent=2))
            if target=='unreal':
                archive.write(REPO/'unreal/scripts/assemble_unreal58_rooms.py','assemble_unreal58_rooms.py')
                instructions=('Unreal 5.8: extract the whole folder. Open your saved original chair demo with its Display chair actor. '
                    'Stop simulation and save the level. Tools > Execute Python Script > assemble_unreal58_rooms.py. '
                    'The script creates new maps using your reviewed chair asset. Inspect the maps, then Alt+S to simulate with Chaos. '
                    'Import the resulting Saved/EmergencyPOC/room-setup-*.json into the workspace. '
                    'Assembly reports do not prove a successful physics simulation. No chair binary is included.')
            else:
                archive.write(REPO/'scripts/blender/assemble_scenario_rooms.py','assemble_scenario_rooms.py')
                archive.write(REPO/'scripts/blender/studio_worker.py','studio_worker.py')
                instructions=('Portable spatial batch. JSON and SVG previews replay without an LLM call. '
                    'Use the local Blender worker in FIELDWORK, or run studio_worker.py in background Blender 5.1 '
                    'with arguments: package_folder prepared_chair.blend output_folder. Original chair file is never edited.')
            archive.writestr('README.txt',instructions)
        return destination

    def import_unreal_report(self, job_id, report, evidence='user_imported_report'):
        job=self.ready(job_id)
        if evidence=='user_imported_report' and any(s.get('status') in ('queued','running') for s in job.get('pipeline',{}).values()):
            raise ValueError('Wait for the active worker before importing a report.')
        if report.get('stage')!='room_setup_complete':
            raise ValueError('Expected a successful Unreal room assembly report.')
        binding=report.get('binding',{})
        expected=json.loads((self.service.directory/job_id/'manifest.json').read_text(encoding='utf-8'))
        rooms=binding.get('rooms',[])
        if binding.get('job_id')!=job_id or len(rooms)!=len(job['scenes']):
            raise ValueError('Report belongs to a different batch.')
        if {r.get('file'):r.get('sha256') for r in rooms}!={s['scene_id']+'.json':expected['files_sha256'][s['scene_id']+'.json'] for s in job['scenes']}:
            raise ValueError('Report specification hashes do not match this batch.')
        maps=report.get('maps',[])
        if len(maps)!=len(job['scenes']) or any(not isinstance(m,dict) or not isinstance(m.get('path'),str) or not m['path'].startswith('/Game/') for m in maps):
            raise ValueError('Report has invalid map entries.')
        value={'status':'assembly_reported','message':'Matching Unreal assembly report imported. Chaos playback still needs observation.',
            'maps':[m['path'] for m in maps], 'simulation_verified':False,'evidence':evidence}
        self.update(job_id,'unreal',value)
        return self.service.get(job_id)
