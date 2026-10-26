"""Description/dispatch binding, uncertain submission recovery and MCP boundaries."""
import asyncio
import io
import json
import subprocess
import sys
import zipfile

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from mcp import ClientSession
from mcp.client.stdio import stdio_client

from arc.scripts.automation_contract import (
    IMAGE_SETTINGS,
    prompt_request,
    reference_prompt,
    sha,
    validate_prompt,
)
from backend.app.api.assets import create_asset_router
from backend.app.studio.arc_transport import ArcConnectionError, ArcTransport
from backend.app.studio.asset_automation import AssetAutomation
from backend.app.studio.assets import AssetLibrary
from backend.app.studio.blender_client import server_parameters
from backend.app.studio.service import SceneBatchService
from backend.tests.test_asset_library import body, result_for


def design():
    value = body()
    value.pop('reference_png_base64')
    return value


class Transport:
    def __init__(self):
        self.calls = []
        self.download = b''
        self.interrupt = False
        self.download_interrupt = False
        self.state = 'COMPLETED'

    def check(self):
        return {'ok': True}

    def call(self, action, dispatch, value=None):
        self.calls.append(action)
        if action == 'submit':
            if self.interrupt:
                self.interrupt = False
                raise ValueError('Connection interrupted after submission.')
            return {'job_id': '100'}
        if action == 'download':
            if self.download_interrupt:
                self.download_interrupt = False
                raise ArcConnectionError('Result transfer interrupted.')
            return self.download
        return {'dispatch': dispatch, 'job_id': '100', 'state': self.state, 'exit_code': '0:0',
                'phase': 'packaged', 'result_ready': True}


def package(job, asset, mutate=None):
    files = {'prompt.json': json.dumps(job['prompt']).encode(), 'result.zip': result_for(asset),
             'image-LICENSE.md': b'Explicit offline fixture license',
             'image-manifest.json': json.dumps({'stage': 'reference_generated', 'settings': IMAGE_SETTINGS,
                 'prompt': reference_prompt(job['prompt']), 'seed': 42,
                 'reference_sha256': asset['request']['reference_sha256']}).encode()}
    if mutate:
        mutate(files)
    files['binding.json'] = json.dumps({'contract': 'fieldwork-automation-v1', 'dispatch': job['id'],
                                       'files': {n: sha(raw) for n, raw in files.items()}}).encode()
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w') as archive:
        for name, raw in files.items():
            archive.writestr(name, raw)
    return out.getvalue()


@pytest.fixture
def automation(tmp_path, monkeypatch):
    service = SceneBatchService(tmp_path)
    library = AssetLibrary(service)
    transport = Transport()
    worker = AssetAutomation(library, transport, poll_seconds=.01)
    monkeypatch.setattr(worker.pool, 'submit', lambda fn, *args: None)
    def prepare(key):
        asset = library.get(key)
        asset['blender'] = {'status': 'complete'}
        library.save(asset)
    monkeypatch.setattr(library, 'prepare', prepare)
    yield worker, library, transport
    worker.pool.shutdown(wait=True)
    service.pool.shutdown(wait=True)


def test_prompt_is_bounded_and_revisions_are_part_of_identity():
    request = prompt_request(design())
    assert validate_prompt(request) == request
    for field, value in [('dimensions_m', [float('nan'), 1, 1]), ('seed', True), ('family', 'script')]:
        with pytest.raises(ValueError):
            prompt_request(dict(design(), **{field: value}))
    with pytest.raises(ValueError):
        validate_prompt(dict(request, image_settings=dict(IMAGE_SETTINGS, revision='unverified')))
    with pytest.raises(ValueError):
        prompt_request(dict(design(), command='arbitrary code'))


def test_end_to_end_dispatch_import_and_preparation_gate(automation):
    worker, library, transport = automation
    job = worker.submit(design())
    assert worker.submit(design())['id'] == job['id']
    with pytest.raises(ValueError, match='current asset'):
        worker.submit(dict(design(), seed=43))
    transport.download = package(job, library.create(body()))
    worker.run(job['id'])
    done = worker.get(job['id'])
    assert done['status'] == 'review_ready'
    assert transport.calls == ['submit', 'status', 'download']
    asset = library.get(done['asset_id'])
    assert asset['room_compatible'] is False
    assert (library.directory/asset['id']/'automation-image-manifest.json').is_file()


def test_uncertain_submission_resumes_same_dispatch_without_second_gpu_job(automation):
    worker, library, transport = automation
    job = worker.submit(design())
    transport.interrupt = True
    worker.run(job['id'])
    assert worker.get(job['id'])['status'] == 'connection_lost'
    worker.resume(job['id'])
    transport.download = package(job, library.create(body()))
    worker.run(job['id'])
    assert worker.get(job['id'])['status'] == 'review_ready'
    assert transport.calls.count('submit') == 1


def test_missing_scheduler_evidence_never_resubmits(automation):
    worker, _, transport = automation
    job = worker.submit(design())
    transport.state = 'SUBMISSION_UNKNOWN'
    worker.run(job['id'])
    assert worker.get(job['id'])['status'] == 'submission_unknown'
    worker.resume(job['id'])
    worker.run(job['id'])
    assert transport.calls.count('submit') == 1


def test_download_interruption_resumes_completed_job_without_regenerating(automation):
    worker, library, transport = automation
    job = worker.submit(design())
    transport.download = package(job, library.create(body()))
    transport.download_interrupt = True
    worker.run(job['id'])
    assert worker.get(job['id'])['status'] == 'connection_lost'
    worker.resume(job['id'])
    worker.run(job['id'])
    assert worker.get(job['id'])['status'] == 'review_ready'
    assert transport.calls.count('submit') == 1
    assert transport.calls.count('download') == 2


def test_terminal_failure_is_truthful_and_allows_explicit_new_attempt(automation):
    worker, _, transport = automation
    job = worker.submit(design())
    transport.state = 'FAILED'
    worker.run(job['id'])
    assert worker.get(job['id'])['status'] == 'failed'
    assert worker.submit(design())['id'] != job['id']


def test_shutdown_stops_monitoring_without_another_submission(automation):
    worker, _, transport = automation
    job = worker.submit(design())
    worker.update(job['id'], submission_started=True, job_id='100')
    worker.close()
    worker.run(job['id'])
    assert worker.get(job['id'])['status'] == 'interrupted'
    assert 'submit' not in transport.calls


@pytest.mark.parametrize('mutate', [
    lambda files: files.update({'prompt.json': b'{}'}),
    lambda files: files.update({'image-manifest.json': b'{}'}),
])
def test_different_prompt_or_image_provenance_is_rejected(automation, mutate):
    worker, library, transport = automation
    job = worker.submit(design())
    transport.download = package(job, library.create(body()), mutate)
    worker.run(job['id'])
    assert worker.get(job['id'])['status'] == 'failed'
    assert not library.get(library.list()[1]['id']).get('result_revision')


def test_transport_uses_fixed_noninteractive_verified_ssh_and_rejects_injection(monkeypatch):
    remote = ArcTransport({'ARC_SSH_TARGET': 'verified-alias', 'ARC_REMOTE_REPO': '/home/user/repo'})
    command = remote.command('status', 'a'*32)
    assert 'BatchMode=yes' in command and 'StrictHostKeyChecking=yes' in command
    assert command[-1] == 'cd /home/user/repo && bash arc/scripts/remote_asset_control.sh status '+'a'*32
    for config in ({'ARC_SSH_TARGET': '-oProxyCommand=evil', 'ARC_REMOTE_REPO': '/repo'},
                   {'ARC_SSH_TARGET': 'host', 'ARC_REMOTE_REPO': '/repo; arbitrary'}):
        with pytest.raises(ValueError):
            ArcTransport(config).command('check')
    monkeypatch.setattr(subprocess, 'run', lambda *a, **k: subprocess.CompletedProcess(a, 1, b'', b'PRIVATE-ERROR'))
    with pytest.raises(ValueError) as failure:
        remote.call('check')
    assert 'PRIVATE-ERROR' not in str(failure.value)


def test_real_mcp_handshake_lists_bounded_tools_and_rejects_path_input(tmp_path, monkeypatch):
    monkeypatch.setenv('ARC_LLM_API_KEY', 'PRIVATE-NOT-FOR-BLENDER')
    parameters = server_parameters(tmp_path, sys.executable)
    assert 'ARC_LLM_API_KEY' not in parameters.env
    assert 'PRIVATE-NOT-FOR-BLENDER' not in str(parameters)
    async def exercise():
        async with (stdio_client(parameters) as (reader, writer), ClientSession(reader, writer) as client):
            await client.initialize()
            tools = await client.list_tools()
            assert {t.name for t in tools.tools} == {'inspect_asset', 'prepare_asset'}
            result = await client.call_tool('inspect_asset', {'asset_id': '../private', 'result_revision': 'a'*32})
            assert result.isError
    asyncio.run(exercise())


def test_automation_routes_reject_foreign_origin_and_keep_secrets_out(tmp_path, monkeypatch):
    service = SceneBatchService(tmp_path)
    app = FastAPI()
    app.include_router(create_asset_router(service))
    worker = service.asset_automation
    worker.transport = Transport()
    monkeypatch.setattr(worker.pool, 'submit', lambda fn, *args: None)
    monkeypatch.setenv('ARC_LLM_API_KEY', 'PRIVATE-NOT-A-PROMPT')
    try:
        client = TestClient(app)
        url = '/api/studio/assets/automation'
        config = client.get(url+'/config')
        assert config.status_code == 200 and 'PRIVATE-NOT-A-PROMPT' not in config.text
        assert client.post(url+'/jobs', json=design(), headers={'Origin': 'https://foreign.example'}).status_code == 403
        assert worker.list() == []
        invalid = dict(design(), description='Do not save PRIVATE-NOT-A-PROMPT')
        assert client.post(url+'/jobs', json=invalid).status_code == 400
        created = client.post(url+'/jobs', json=design())
        assert created.status_code == 202
        assert created.json()['status'] == 'queued' and 'job_id' not in created.json()
        assert client.post(url+'/jobs', json=design()).json()['id'] == created.json()['id']
    finally:
        worker.pool.shutdown(wait=True)
        service.pool.shutdown(wait=True)
