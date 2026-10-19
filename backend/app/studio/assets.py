"""Immutable furniture designs and portable ARC generation handoffs."""
import base64
import binascii
import io
import json
import os
import subprocess
import re
import shutil
import struct
import threading
import uuid
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from arc.scripts.asset_request import make_request, sha, validate_png, validate_request
from backend.app.studio.service import REPO, local_settings

BUILTIN = 'hunyuan_wooden_chair_8053348'
RESULT_NAMES = {'asset.glb', 'preview.png', 'shape-manifest.json', 'paint-manifest.json',
    'LICENSE', 'Notice.txt', 'source-patches.diff'}


def check_glb(raw):
    if len(raw) < 24 or len(raw) > 200_000_000 or struct.unpack('<4sII', raw[:12]) != (b'glTF', 2, len(raw)):
        raise ValueError('Expected an embedded GLB 2.0 model smaller than 200 MB.')
    size, kind = struct.unpack('<II', raw[12:20])
    if kind != 0x4e4f534a or size > len(raw)-20:
        raise ValueError('Invalid GLB document.')
    try:
        document = json.loads(raw[20:20+size])
        if document.get('asset', {}).get('version') != '2.0':
            raise ValueError('Invalid GLB asset version.')
        for field in ('images', 'buffers'):
            for item in document.get(field, []):
                uri = item.get('uri', '')
                if uri and not uri.startswith('data:'):
                    raise ValueError('GLB images and buffers must be embedded, with no external files or URLs.')
    except (TypeError, KeyError, AttributeError, UnicodeError, json.JSONDecodeError):
        raise ValueError('Invalid GLB document.') from None


class AssetLibrary:
    def __init__(self, service):
        self.service = service
        self.directory = service.directory / 'asset-library'
        self.directory.mkdir(exist_ok=True)
        self.lock = threading.RLock()
        with service.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS asset_variants (id TEXT PRIMARY KEY, data TEXT NOT NULL)')
            for asset_id, data in db.execute('SELECT id,data FROM asset_variants').fetchall():
                record = json.loads(data)
                if record.get('blender', {}).get('status') in ('queued', 'running'):
                    record['blender'] = {'status': 'interrupted', 'message': 'Backend restarted. Prepare the review copy again.'}
                    db.execute('UPDATE asset_variants SET data=? WHERE id=?', (json.dumps(record), asset_id))

    def builtin(self):
        bound = Path(local_settings()['CHAIR_BLEND']).is_file()
        return {'id': BUILTIN, 'family': 'chair', 'name': 'Wooden dining chair',
            'description': 'The reviewed original Hunyuan wooden chair demo; 19 prepared collision pieces.',
            'dimensions_m': [.542, .633, 1.0], 'status': 'demo_ready' if bound else 'binding_needed',
            'room_compatible': True, 'builtin': True, 'source_shape_job': '8052814', 'source_paint_job': '8053348'}

    def list(self):
        with self.service.connect() as db:
            rows = db.execute('SELECT data FROM asset_variants ORDER BY rowid DESC').fetchall()
        return [self.builtin(), *(json.loads(r[0]) for r in rows)]

    def get(self, asset_id):
        if asset_id == BUILTIN:
            return self.builtin()
        if not re.fullmatch('[a-f0-9]{64}', asset_id):
            raise ValueError('Asset not found.')
        with self.service.connect() as db:
            row = db.execute('SELECT data FROM asset_variants WHERE id=?', (asset_id,)).fetchone()
        if row is None:
            raise ValueError('Asset not found.')
        return json.loads(row[0])

    def save(self, record):
        with self.service.connect() as db:
            db.execute('INSERT OR REPLACE INTO asset_variants VALUES (?, ?)', (record['id'], json.dumps(record)))

    def create(self, body):
        try:
            image = base64.b64decode(body['reference_png_base64'], validate=True)
        except (ValueError, binascii.Error):
            raise ValueError('Invalid PNG upload.') from None
        token = local_settings()['ARC_LLM_API_KEY']
        if token and any(token in str(body.get(k, '')) for k in ('name', 'description')):
            raise ValueError('Remove the credential from the design request. Nothing was saved.')
        value = make_request(body['family'], body['name'], body['description'], body['dimensions_m'], body['seed'], image)
        with self.lock:
            try:
                return dict(self.get(value['asset_id']), reused=True)
            except ValueError:
                pass
            target = self.directory/value['asset_id']
            target.mkdir(exist_ok=True)
            (target/'reference.png').write_bytes(image)
            (target/'request.json').write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')
            record = {k: value[k] for k in ('family', 'name', 'description', 'dimensions_m', 'seed')}
            record.update(id=value['asset_id'], status='ready_for_arc', room_compatible=False,
                created_at=datetime.now(UTC).isoformat(), request=value)
            self.save(record)
        return dict(record, reused=False)

    def bundle(self, asset_id):
        record = self.get(asset_id)
        if record.get('builtin'):
            raise ValueError('The original chair already has a generation history.')
        target = self.directory/asset_id
        out = io.BytesIO()
        with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as archive:
            for name in ('request.json', 'reference.png'):
                archive.write(target/name, name)
        return out.getvalue()

    def file(self, asset_id, name):
        record = self.get(asset_id)
        if record.get('builtin') or name not in ('reference.png', 'preview.png', 'asset.glb', 'result.json'):
            raise ValueError('Asset file unavailable.')
        folder = self.directory/asset_id
        if name != 'reference.png':
            if not record.get('result_revision'):
                raise ValueError('Generate this asset on ARC and import its result first.')
            folder = folder/'results'/record['result_revision']
        path = folder/name
        if not path.is_file():
            raise ValueError('Asset file unavailable.')
        return path

    def import_result(self, asset_id, raw):
        if len(raw) > 240_000_000:
            raise ValueError('Result ZIP exceeds 240 MB.')
        record = self.get(asset_id)
        if record.get('builtin'):
            raise ValueError('The original chair cannot be replaced here.')
        expected = record['request']
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                names = archive.namelist()
                allowed = RESULT_NAMES | {'result.json', 'request.json', 'reference.png'}
                if set(names) != allowed or len(names) != len(allowed):
                    raise ValueError('Result ZIP has unexpected or missing files. Use the ARC variant exporter.')
                if any(info.file_size > 200_000_000 for info in archive.infolist()) or sum(i.file_size for i in archive.infolist()) > 240_000_000:
                    raise ValueError('Expanded result ZIP is too large.')
                files = {name: archive.read(name) for name in names}
            request = json.loads(files['request.json'])
            validate_request(request, files['reference.png'])
            if request != expected:
                raise ValueError('This result belongs to a different design request.')
            result = json.loads(files['result.json'])
            if result.get('contract') != 'furniture-result-v1' or result.get('asset_id') != asset_id or result.get('stage') != 'completed':
                raise ValueError('This generation result is incomplete or mismatched.')
            if result.get('files') != {name: sha(files[name]) for name in RESULT_NAMES}:
                raise ValueError('Result file checksums do not match.')
            shape = json.loads(files['shape-manifest.json'])
            paint = json.loads(files['paint-manifest.json'])
            if shape.get('stage') != 'completed' or paint.get('stage') != 'completed' or not paint.get('textures_generated'):
                raise ValueError('Both shape and texture stages must be complete.')
            if shape.get('input_sha256') != expected['reference_sha256'] or shape.get('seed') != expected['seed']:
                raise ValueError('Shape provenance does not match the reference image and seed.')
            if shape.get('model_revision') != expected['settings']['shape_revision'] or paint.get('paint_revision') != expected['settings']['paint_revision']:
                raise ValueError('Generation used different model revisions.')
            if shape.get('source_revision') != expected['settings']['source_revision'] or paint.get('source_revision') != expected['settings']['source_revision'] or paint.get('dino_revision') != expected['settings']['dino_revision']:
                raise ValueError('Generation source or DINO revision does not match this request.')
            if paint.get('source_job_id') != shape.get('job_id'):
                raise ValueError('Texture provenance refers to a different shape run.')
            validate_png(files['preview.png'])
            check_glb(files['asset.glb'])
        except (zipfile.BadZipFile, KeyError, TypeError, AttributeError, UnicodeError, json.JSONDecodeError, RuntimeError, NotImplementedError):
            raise ValueError('Invalid ARC result package. Use the variant exporter and retry.') from None
        with self.lock:
            record = self.get(asset_id)
            if record.get('result_revision'):
                raise ValueError('This variant already has a result. Change the seed or design to make another version.')
            revision = uuid.uuid4().hex
            folder = self.directory/asset_id/'results'/revision
            folder.mkdir(parents=True)
            try:
                for name, data in files.items():
                    (folder/name).write_bytes(data)
                record.update(status='generated_review_needed', result_revision=revision,
                    imported_at=datetime.now(UTC).isoformat(), result=result,
                    next_step='Inspect the model in Blender; dimensions, orientation and collision pieces need review.')
                self.save(record)
            except Exception:
                shutil.rmtree(folder)
                raise
        return record


    def prepare(self, asset_id):
        with self.lock:
            record = self.get(asset_id)
            if record.get('builtin') or not record.get('result_revision'):
                raise ValueError('Import this variant’s ARC result first.')
            if record.get('blender', {}).get('status') in ('queued', 'running'):
                raise ValueError('This variant is already being prepared.')
            executable = local_settings()['BLENDER_EXECUTABLE']
            if not executable or not Path(executable).is_file():
                raise ValueError('Set BLENDER_EXECUTABLE in backend/.env first; use Connections to check the path.')
            run = uuid.uuid4().hex
            record['blender'] = {'status': 'queued', 'run': run, 'message': 'Waiting for the local Blender worker.'}
            self.save(record)
            self.service.pool.submit(self.run_prepare, asset_id, run, executable)
        return record

    def run_prepare(self, asset_id, run, executable):
        with self.lock:
            record = self.get(asset_id)
            record['blender'].update(status='running', message='Blender is making a separate review copy.')
            self.save(record)
        folder = self.directory/asset_id
        output = folder/'blender'/run
        output.parent.mkdir(exist_ok=True)
        command = [executable, '--background', '--factory-startup', '--python-exit-code', '1',
            '--python', str(REPO/'scripts/blender/prepare_furniture_variant.py'), '--',
            '--source', str(self.file(asset_id, 'asset.glb')), '--request', str(folder/'request.json'),
            '--output', str(output)]
        env = {k:v for k,v in os.environ.items() if k not in ('ARC_LLM_API_KEY','OPENAI_API_KEY','HF_TOKEN')}
        try:
            result = subprocess.run(command, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=1800, check=False)
            if result.returncode != 0 or not (output/'furniture-review.blend').is_file():
                raise ValueError('Blender worker failed.')
            report = json.loads((output/'report.json').read_text(encoding='utf-8'))
            if report['asset_id'] != asset_id or report.get('room_compatible') is not False:
                raise ValueError('Unexpected Blender report.')
            state = {'status': 'complete', 'run': run, 'report': report,
                'message': 'Review copy ready. Inspect scale, orientation and materials; collision pieces are still needed.'}
        except Exception:
            state = {'status': 'failed', 'run': run,
                'message': 'Blender could not prepare this model. Check the executable and imported GLB, then retry.'}
        with self.lock:
            record = self.get(asset_id)
            record['blender'] = state
            self.save(record)

    def blender_file(self, asset_id, name):
        record = self.get(asset_id)
        state = record.get('blender', {})
        if state.get('status') != 'complete' or name not in ('furniture-review.blend', 'report.json'):
            raise ValueError('Blender review output is not ready.')
        if not re.fullmatch('[a-f0-9]{32}', state.get('run', '')):
            raise ValueError('Blender review output is not ready.')
        path = self.directory/asset_id/'blender'/state['run']/name
        if not path.is_file():
            raise ValueError('Blender review file is missing.')
        return path
