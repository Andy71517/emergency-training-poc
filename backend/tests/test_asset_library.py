"""Variant identity, untrusted handoffs and ARC/local review boundaries."""
import base64
import io
import json
import shutil
import struct
import subprocess
import sys
import zipfile
import zlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from arc.scripts.asset_request import make_request, sha
from backend.app.api.assets import create_asset_router
from backend.app.studio.assets import RESULT_NAMES, AssetLibrary, check_glb
from backend.app.studio.service import REPO, SceneBatchService


def png():
    def chunk(kind, data):
        return struct.pack('>I', len(data))+kind+data+struct.pack('>I', zlib.crc32(kind+data)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR', struct.pack('>IIBBBBB',64,64,8,2,0,0,0))+chunk(b'IDAT',zlib.compress((b'\0'+b'\x80'*192)*64))+chunk(b'IEND',b'')


def glb(uri=None):
    value={'asset':{'version':'2.0'}, 'scenes':[{}], 'scene':0}
    if uri:
        value['images']=[{'uri':uri}]
    raw=json.dumps(value).encode()
    raw+=b' '*((-len(raw))%4)
    return struct.pack('<4sIIII',b'glTF',2,20+len(raw),len(raw),0x4e4f534a)+raw


def body(**kwargs):
    return dict(family='couch',name='Charcoal sofa',description='Two seat couch, straight arms and short dark legs.',
        dimensions_m=[1.8,.85,.85],seed=42,reference_png_base64=base64.b64encode(png()).decode(),**kwargs)


def result_for(record, mutate=None):
    request=record['request']
    settings=request['settings']
    shape={'stage':'completed','job_id':'100','seed':request['seed'],
        'input_sha256':request['reference_sha256'],'model_revision':settings['shape_revision'],
        'source_revision':settings['source_revision']}
    paint={'stage':'completed','job_id':'100','source_job_id':'100','textures_generated':True,
        'paint_revision':settings['paint_revision'],'source_revision':settings['source_revision'],
        'dino_revision':settings['dino_revision']}
    files={'request.json':json.dumps(request).encode(),'reference.png':png(),
        'asset.glb':glb(),'preview.png':png(),'shape-manifest.json':json.dumps(shape).encode(),
        'paint-manifest.json':json.dumps(paint).encode(),'LICENSE':b'fixture license',
        'Notice.txt':b'fixture notice','source-patches.diff':b'fixture patches'}
    if mutate:
        mutate(files)
    result={'contract':'furniture-result-v1','asset_id':record['id'],'stage':'completed',
        'files':{name:sha(files[name]) for name in RESULT_NAMES}}
    files['result.json']=json.dumps(result).encode()
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w') as archive:
        for name,raw in files.items():
            archive.writestr(name,raw)
    return out.getvalue()


@pytest.fixture
def library(tmp_path):
    service=SceneBatchService(tmp_path)
    lib=AssetLibrary(service)
    yield lib
    service.pool.shutdown(wait=True)


def test_variants_are_distinct_and_identical_requests_are_reused(library):
    with ThreadPoolExecutor(4) as pool:
        records=list(pool.map(lambda _:library.create(body()),range(4)))
    assert len({r['id'] for r in records})==1
    assert sum(not r['reused'] for r in records)==1
    for key,value in [('family','chair'),('name','Leather two-seat sofa'),('seed',43),('dimensions_m',[2,.85,.85])]:
        payload=body();payload[key]=value
        assert library.create(payload)['id']!=records[0]['id']
    assert AssetLibrary(library.service).get(records[0]['id'])['status']=='ready_for_arc'


def test_request_package_is_validated_by_arc_cli(library,tmp_path):
    asset=library.create(body());path=tmp_path/'request.zip';path.write_bytes(library.bundle(asset['id']))
    run=subprocess.run([sys.executable,str(REPO/'arc/scripts/hunyuan_variant.py'),'unpack',str(path),str(tmp_path/'requests')],capture_output=True,text=True,check=True)
    folder=Path(run.stdout.strip())
    assert folder.name==asset['id']
    assert json.loads((folder/'request.json').read_bytes())==asset['request']
    assert len(zipfile.ZipFile(path).namelist())==2


def test_import_matches_variant_preserves_result_and_review_gate(library):
    asset=library.create(body())
    result=library.import_result(asset['id'],result_for(asset))
    assert result['status']=='generated_review_needed'
    assert result['room_compatible'] is False
    assert library.file(asset['id'],'asset.glb').read_bytes()==glb()
    with pytest.raises(ValueError,match='already has a result'):
        library.import_result(asset['id'],result_for(asset))
    with pytest.raises(ValueError):
        library.file(asset['id'],'../../jobs.sqlite3')


def test_other_request_corrupt_hash_and_path_escape_rejected(library):
    asset=library.create(body());other=body();other['seed']=50;second=library.create(other)
    with pytest.raises(ValueError,match='different design'):
        library.import_result(second['id'],result_for(asset))
    with pytest.raises(ValueError,match='stages must be complete'):
        library.import_result(asset['id'],result_for(asset,lambda f:f.update({'shape-manifest.json':b'{}'})))
    out=io.BytesIO()
    with zipfile.ZipFile(out,'w') as archive:
        archive.writestr('../outside.txt','no')
    with pytest.raises(ValueError,match='unexpected or missing'):
        library.import_result(asset['id'],out.getvalue())
    assert not (library.directory.parent/'outside.txt').exists()


def test_external_model_resources_and_invalid_reference_rejected(library):
    for uri in ('https://example.com/image.png','file:///private.png','../../private.png'):
        with pytest.raises(ValueError,match='embedded'):
            check_glb(glb(uri))
    with pytest.raises(ValueError,match='PNG'):
        make_request('couch','Sofa','Long enough description',[1,1,1],42,b'not an image')
    for dimension in (float('nan'),float('inf'),0,5,True):
        with pytest.raises(ValueError):
            make_request('couch','Sofa','Long enough description',[dimension,1,1],42,png())


def test_credential_not_saved(library,monkeypatch):
    monkeypatch.setenv('ARC_LLM_API_KEY','PRIVATE-FIXTURE-SECRET')
    payload=body();payload['description']='Do not save PRIVATE-FIXTURE-SECRET here'
    with pytest.raises(ValueError,match='credential'):
        library.create(payload)
    assert len(library.list())==1


def test_asset_routes_local_origin_upload_validation_and_download(library):
    app=FastAPI();app.include_router(create_asset_router(library.service));client=TestClient(app)
    assert client.post('/api/studio/assets',json=body(),headers={'Origin':'https://example.com'}).status_code==403
    response=client.post('/api/studio/assets',json=body());assert response.status_code==201
    asset=response.json()
    assert client.get(f"/api/studio/assets/{asset['id']}/request.zip").status_code==200
    assert client.post(f"/api/studio/assets/{asset['id']}/result",content=b'broken').status_code==400
    response=client.post(f"/api/studio/assets/{asset['id']}/result",content=result_for(asset))
    assert response.status_code==200
    assert client.get(f"/api/studio/assets/{asset['id']}/files/asset.glb").status_code==200
    assert client.post(f"/api/studio/assets/{asset['id']}/prepare").status_code in (202,400)


def test_arc_sbatch_syntax_and_pinned_runtime_paths():
    for relative in ('arc/scripts/submit_hunyuan_variant.sh','arc/jobs/generate_hunyuan_variant.sbatch'):
        subprocess.run([shutil.which('bash') or 'bash', '-n', (REPO/relative).as_posix()], check=True)
    text=(REPO/'arc/jobs/generate_hunyuan_variant.sbatch').read_text()
    # The unchanged shape exporter finds LICENSE via the first PYTHONPATH entry.
    assert 'PYTHONPATH=/workspace/hunyuan21/source/hy3dshape:/project/arc/scripts' in text
    assert 'flock -n 9' in text
    assert 'conda activate /workspace/hunyuan21/texture-environment' in text


def test_arc_export_import_round_trip_preserves_notices(library,tmp_path):
    asset=library.create(body())
    request_dir=tmp_path/'request';request_dir.mkdir()
    (request_dir/'request.json').write_text(json.dumps(asset['request']))
    (request_dir/'reference.png').write_bytes(png())
    run=tmp_path/'run';(run/'shape').mkdir(parents=True);(run/'paint').mkdir()
    with zipfile.ZipFile(io.BytesIO(result_for(asset))) as archive:
        (run/'shape/manifest.json').write_bytes(archive.read('shape-manifest.json'))
        (run/'paint/manifest.json').write_bytes(archive.read('paint-manifest.json'))
        (run/'paint/chair-textured.glb').write_bytes(archive.read('asset.glb'))
        for name in ('preview.png','LICENSE','Notice.txt','source-patches.diff'):
            (run/'paint'/name).write_bytes(archive.read(name))
    subprocess.run([sys.executable,str(REPO/'arc/scripts/hunyuan_variant.py'),'package',str(request_dir),str(run)],check=True,capture_output=True)
    imported=library.import_result(asset['id'],(run/'result.zip').read_bytes())
    assert imported['status']=='generated_review_needed'
    assert imported['result']['collision_mesh_created'] is False
    assert imported['result']['dimensions_are_requested_not_measured'] is True
    with zipfile.ZipFile(run/'result.zip') as archive:
        assert archive.read('LICENSE')==b'fixture license'


def test_blender_review_worker_keeps_credentials_out_and_persists_gate(library,tmp_path,monkeypatch):
    asset=library.create(body());library.import_result(asset['id'],result_for(asset))
    executable=tmp_path/'blender';executable.write_text('fixture')
    monkeypatch.setenv('BLENDER_EXECUTABLE',str(executable))
    monkeypatch.setenv('ARC_LLM_API_KEY','SECRET-NOT-FOR-BLENDER')
    def worker(command,**kwargs):
        assert 'ARC_LLM_API_KEY' not in kwargs['env']
        assert all('SECRET-NOT-FOR-BLENDER' not in x for x in command)
        output=Path(command[command.index('--output')+1]);output.mkdir()
        (output/'furniture-review.blend').write_bytes(b'fixture only')
        (output/'report.json').write_text(json.dumps({'asset_id':asset['id'],'room_compatible':False}))
        return subprocess.CompletedProcess(command,0)
    monkeypatch.setattr('backend.app.studio.assets.subprocess.run',worker)
    library.prepare(asset['id'])
    library.service.pool.shutdown(wait=True)
    assert library.get(asset['id'])['blender']['status']=='complete'
    assert library.get(asset['id'])['room_compatible'] is False
    assert library.blender_file(asset['id'],'report.json').is_file()


@pytest.mark.parametrize('failure', ['timeout', 'invalid_report', 'missing_output', 'missing_source'])
def test_blender_review_failure_is_persisted_and_retryable(library, tmp_path, monkeypatch, failure):
    asset = library.create(body())
    library.import_result(asset['id'], result_for(asset))
    executable = tmp_path / 'blender'
    executable.write_text('fixture')
    monkeypatch.setenv('BLENDER_EXECUTABLE', str(executable))

    def worker(command, **kwargs):
        if failure == 'timeout':
            raise subprocess.TimeoutExpired(command, 1800)
        output = Path(command[command.index('--output') + 1])
        output.mkdir()
        if failure == 'invalid_report':
            (output / 'furniture-review.blend').write_bytes(b'fixture only')
            (output / 'report.json').write_text('[]')
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr('backend.app.studio.assets.subprocess.run', worker)
    if failure == 'missing_source':
        library.file(asset['id'], 'asset.glb').unlink()
    # Execute queued work inline so the persisted failure is immediately observable.
    monkeypatch.setattr(library.service.pool, 'submit', lambda fn, *args: fn(*args))
    library.prepare(asset['id'])
    first = library.get(asset['id'])
    assert first['blender']['status'] == 'failed'
    assert first['room_compatible'] is False
    with pytest.raises(ValueError, match='not ready'):
        library.blender_file(asset['id'], 'furniture-review.blend')
    library.prepare(asset['id'])
    again = library.get(asset['id'])
    assert again['blender']['status'] == 'failed'
    assert again['blender']['run'] != first['blender']['run']
