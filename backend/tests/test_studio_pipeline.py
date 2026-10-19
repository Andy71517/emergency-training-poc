"""Cross-stage contracts: replay, portable handoff, report binding and worker failure."""
import io
import json
import time
import urllib.error
import zipfile

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.api.studio import create_studio_router
from backend.app.studio.service import SceneBatchService
from backend.tests.test_studio import plan, wait


def client_service(tmp_path, monkeypatch):
    monkeypatch.setenv('ARC_LLM_API_KEY','sk-pipeline-private')
    calls=[]
    def planner(*args, **kwargs):
        calls.append(True)
        return plan(), {'provider':'offline_test'}
    service=SceneBatchService(tmp_path,planner)
    app=FastAPI()
    app.include_router(create_studio_router(service))
    return TestClient(app),service,calls


def test_replay_bundle_report_and_file_boundaries(tmp_path,monkeypatch):
    client,service,calls=client_service(tmp_path,monkeypatch)
    with client:
        job=wait(service,service.submit('Three classroom layouts',3,42)['id'])
        base=f"/api/studio/jobs/{job['id']}"
        replay=client.post(base+'/replay',json={'seed':99})
        assert replay.status_code==202
        again=wait(service,replay.json()['id'])
        assert again['status']=='review_ready' and again['seed']==99 and len(calls)==1
        assert again['scenes']!=job['scenes']
        response=client.get(base+'/bundle/unreal')
        assert response.status_code==200
        archive=zipfile.ZipFile(io.BytesIO(response.content))
        binding=json.loads(archive.read('room-package.json'))
        assert binding['job_id']==job['id']
        assert 'assemble_unreal58_rooms.py' in archive.namelist()
        assert b'sk-pipeline-private' not in response.content
        report={'stage':'room_setup_complete','binding':binding,
                'maps':[{'path':'/Game/Test/'+s['scene_id']} for s in job['scenes']]}
        result=client.post(base+'/unreal-report',json=report)
        assert result.status_code==200
        assert result.json()['pipeline']['unreal']['simulation_verified'] is False
        binding['rooms'][0]['sha256']='altered'
        assert client.post(base+'/unreal-report',json=report).status_code==400
        assert client.post(base+'/unreal-report',json=[]).status_code==400
        assert client.post(base+'/replay',headers={'origin':'https://foreign.example'},json={'seed':1}).status_code==403
        assert client.get(base+'/blender-files/rooms.blend').status_code==404
        assert client.get(base+'/bundle/unknown').status_code==404
    service.pool.shutdown(wait=True)


def test_network_failure_is_actionable_and_worker_failure_persists(tmp_path,monkeypatch):
    client,service,_=client_service(tmp_path,monkeypatch)
    def disconnected(*args,**kwargs):
        raise urllib.error.URLError('sensitive transport details')
    service.planner=disconnected
    job=wait(service,service.submit('Three classroom layouts',3,42)['id'])
    assert 'VPN' in job['error'] and 'sensitive' not in job['error']
    service.planner=lambda *a,**k:(plan(),{'provider':'offline_test'})
    job=wait(service,service.submit('Three classroom layouts',3,42)['id'])
    executable=tmp_path/'fake-blender.exe';executable.touch()
    chair=tmp_path/'chair.blend';chair.touch()
    monkeypatch.setenv('BLENDER_EXECUTABLE',str(executable))
    monkeypatch.setenv('CHAIR_BLEND',str(chair))
    def broken(*args,**kwargs):
        assert 'ARC_LLM_API_KEY' not in kwargs['env']
        assert isinstance(args[0],list)
        raise OSError('private process details')
    monkeypatch.setattr('backend.app.studio.pipeline.subprocess.run',broken)
    with client:
        base=f"/api/studio/jobs/{job['id']}"
        assert client.post(base+'/blender').status_code==202
        for _ in range(100):
            state=service.get(job['id']).get('pipeline',{}).get('blender',{})
            if state.get('status')=='failed':break
            time.sleep(.01)
        assert state['status']=='failed' and 'private' not in state['message']
    service.pool.shutdown(wait=True)


def test_editor_queue_and_report_roundtrip(tmp_path,monkeypatch):
    client,service,_=client_service(tmp_path,monkeypatch)
    job=wait(service,service.submit('Three classroom layouts',3,42)['id'])
    queue=tmp_path/'engine';queue.mkdir()
    (queue/'heartbeat.json').write_text(json.dumps({'time':time.time(),'busy':False,'engine_version':'5.8.test'}))
    base=f"/api/studio/jobs/{job['id']}"
    with client:
        r=client.post(base+'/engine/assemble')
        assert r.status_code==202
        assert client.post(base+'/engine/simulate').status_code==400
        command=json.loads(next(queue.glob('*.command.json')).read_text())
        binding=json.loads((tmp_path/job['id']/'room-package.json').read_text())
        maps=[{'path':'/Game/EmergencyPOC/Rooms_test/Maps/'+s['scene_id']} for s in job['scenes']]
        (queue/(command['id']+'.result.json')).write_text(json.dumps({'ok':True,'action':'assemble','job_id':job['id'],
            'report':{'stage':'room_setup_complete','binding':binding,'maps':maps}}))
        state=client.get('/api/studio/jobs').json()[0]['pipeline']['unreal']
        assert state['status']=='assembly_reported' and state['evidence']=='local_editor_bridge'
        next(queue.glob('*.command.json')).unlink()
        assert client.post(base+'/engine/simulate').status_code==202
        command=json.loads(next(queue.glob('*.command.json')).read_text())
        result={'ok':True,'action':'simulate','job_id':job['id'],'observations':[
            {'map':m['path'],'maximum_endpoint_displacement_m':0.001,'chairs_observed':12} for m in maps]}
        (queue/(command['id']+'.result.json')).write_text(json.dumps(result))
        state=client.get('/api/studio/jobs').json()[0]['pipeline']['simulation']
        assert state['status']=='playback_reported' and state['contacts_measured'] is False
        assert client.get(base+'/chaos-report').status_code==200
        assert client.post(base+'/engine/arbitrary-command').status_code==400
    service.pool.shutdown(wait=True)
