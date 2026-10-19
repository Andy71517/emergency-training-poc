"""Duplicate suppression, active-job protection and reversible batch removal."""
import threading
from concurrent.futures import ThreadPoolExecutor

from backend.tests.test_studio import wait
from backend.tests.test_studio_pipeline import client_service


def test_duplicate_requests_use_one_model_call_and_fresh_is_explicit(tmp_path,monkeypatch):
    client,service,calls=client_service(tmp_path,monkeypatch)
    release=threading.Event()
    planner=service.planner
    def delayed(*args,**kwargs):
        release.wait(3)
        return planner(*args,**kwargs)
    service.planner=delayed
    with ThreadPoolExecutor(max_workers=4) as pool:
        jobs=list(pool.map(lambda _:service.submit('Same classroom prompt',3,42),range(4)))
    assert len({j['id'] for j in jobs})==1 and sum(not j['reused'] for j in jobs)==1
    with client:
        base='/api/studio/jobs/'+jobs[0]['id']
        assert client.post(base+'/trash').status_code==400
        release.set()
        original=wait(service,jobs[0]['id'])
        body={'prompt':'  Same classroom prompt\r\n','count':3,'seed':42}
        assert client.post('/api/studio/jobs/match',json=body).json()['id']==original['id']
        reused=client.post('/api/studio/jobs',json=body).json()
        assert reused['reused'] is True and len(calls)==1
        fresh=client.post('/api/studio/jobs',json={**body,'force_new':True}).json()
        assert fresh['id']!=original['id']
        assert wait(service,fresh['id'])['status']=='review_ready' and len(calls)==2
        assert client.post('/api/studio/jobs/match',json={**body,'seed':43}).json() is None
        assert client.post('/api/studio/jobs/match',json={**body,'count':2}).json() is None
    service.pool.shutdown(wait=True)


def test_trash_restore_and_replay_do_not_inherit_worker_outputs(tmp_path,monkeypatch):
    client,service,_=client_service(tmp_path,monkeypatch)
    job=wait(service,service.submit('A recoverable classroom batch',3,42)['id'])
    job['pipeline']={'unreal':{'status':'assembly_reported','maps':['/Game/Old']},
                     'video':{'status':'complete','run':'a'*32,'clips':[]}}
    service.save(job)
    base='/api/studio/jobs/'+job['id']
    with client:
        replay=client.post(base+'/replay',json={'seed':43}).json()
        replay=wait(service,replay['id'])
        assert replay['pipeline']=={}
        assert client.post(base+'/trash',headers={'origin':'https://foreign.example'}).status_code==403
        assert client.post(base+'/trash').status_code==200
        assert job['id'] not in {j['id'] for j in client.get('/api/studio/jobs').json()}
        assert client.get('/api/studio/trash').json()[0]['id']==job['id']
        assert client.get(base).status_code==404
        assert client.get(base+'/files/room_001.svg').status_code==404
        assert (tmp_path/job['id']/'room_001.svg').is_file()
        assert client.post('/api/studio/jobs/match',json={'prompt':job['prompt'],'count':3,'seed':42}).json() is None
        restored=client.post(base+'/restore').json()
        assert 'trashed_at' not in restored
        assert client.get(base+'/files/room_001.svg').status_code==200
        assert restored['pipeline']['video']['run']=='a'*32
    service.pool.shutdown(wait=True)
