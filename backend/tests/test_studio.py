"""Persistent real-planner adapter integration tested with explicit offline fixtures."""
import time
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.api.studio import create_studio_router
from backend.app.studio.service import SceneBatchService


def plan():
    return {'title':'Offline test classroom','room_width_m':8,'room_depth_m':8,
            'room_height_m':3,'door_width_m':1.2,'aisle_width_m':1.6,'chairs_per_room':12,
            'variant_conditions':['clear','clear','obstructed'],
            'asset_ids':['hunyuan_wooden_chair_8053348'],'assumptions':['Offline fixture'],
            'unsupported_requests':[]}


def wait(service,job_id):
    for _ in range(200):
        job=service.get(job_id)
        if job['status'] in ('failed','review_ready'):
            return job
        time.sleep(.01)
    raise AssertionError('Worker did not finish')


def test_persisted_artifacts_and_key_boundary(tmp_path,monkeypatch):
    monkeypatch.setenv('ARC_LLM_API_KEY','sk-private-test-key')
    def planner(prompt,count,model,token):
        assert token=='sk-private-test-key'
        return plan(),{'provider':'offline_test_fixture'}
    service=SceneBatchService(tmp_path,planner)
    app=FastAPI();app.include_router(create_studio_router(service))
    with TestClient(app) as client:
        r=client.post('/api/studio/jobs',json={'prompt':'Three classrooms with chairs','count':3,'seed':42})
        assert r.status_code==202
        job=wait(service,r.json()['id'])
        assert job['status']=='review_ready' and len(job['scenes'])==3
        assert client.get(f"/api/studio/jobs/{job['id']}/files/room_001.svg").status_code==200
        assert client.get(f"/api/studio/jobs/{job['id']}/files/jobs.sqlite3").status_code==404
        assert client.get('/api/studio/jobs/not-an-id').status_code==404
        assert 'sk-private-test-key' not in client.get('/api/studio/jobs').text
        assert 'sk-private-test-key' not in client.get('/api/studio/config').text
        assert client.post('/api/studio/jobs',headers={'origin':'https://foreign.example'},json={'prompt':'Three classrooms with chairs','count':3,'seed':42}).status_code==403
        assert client.post('/api/studio/jobs',json={'prompt':'The key is sk-private-test-key','count':3,'seed':42}).status_code==400
        assert client.post('/api/studio/jobs',json={'prompt':'Three classrooms with chairs','count':True,'seed':42}).status_code==422
    service.pool.shutdown(wait=True)
    reopened=SceneBatchService(tmp_path,planner)
    assert reopened.get(job['id'])['status']=='review_ready'
    assert all(b'sk-private-test-key' not in p.read_bytes() for p in Path(tmp_path).rglob('*') if p.is_file())
    reopened.pool.shutdown(wait=True)


def test_failure_is_persisted_without_secret(tmp_path,monkeypatch):
    monkeypatch.setenv('ARC_LLM_API_KEY','sk-private-test-key')
    def broken(*args,**kwargs):
        raise ValueError('Secret echo sk-private-test-key')
    service=SceneBatchService(tmp_path,broken)
    job=wait(service,service.submit('Three classrooms with chairs',3,42)['id'])
    assert job['status']=='failed'
    assert 'sk-' not in job['error']
    service.pool.shutdown(wait=True)
