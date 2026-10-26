"""Persistent one-asset automation; network uncertainty never triggers a second job."""
import base64
import io
import json
import threading
import time
import uuid
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

from arc.scripts.automation_contract import canonical, prompt_request, reference_prompt, sha
from backend.app.studio.arc_transport import ArcConnectionError, ArcTransport
from backend.app.studio.service import local_settings

ACTIVE = {'queued', 'connecting', 'submitting', 'remote', 'importing', 'preparing'}
RECOVERABLE = {'connection_lost', 'interrupted', 'submission_unknown'}


class AssetAutomation:
    def __init__(self, library, transport=None, poll_seconds=20):
        self.library = library
        self.service = library.service
        self.transport = transport or ArcTransport()
        self.poll_seconds = poll_seconds
        self.lock = threading.RLock()
        self.stopping = threading.Event()
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix='arc-assets')
        with self.service.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS asset_jobs (id TEXT PRIMARY KEY, data TEXT NOT NULL)')
            for key, raw in db.execute('SELECT id,data FROM asset_jobs').fetchall():
                job = json.loads(raw)
                if job['status'] in ACTIVE:
                    job.update(status='interrupted', message='Backend restarted. Resume this saved dispatch.')
                    db.execute('UPDATE asset_jobs SET data=? WHERE id=?', (json.dumps(job), key))

    def list(self):
        with self.service.connect() as db:
            return [json.loads(r[0]) for r in db.execute('SELECT data FROM asset_jobs ORDER BY rowid DESC').fetchall()]

    def close(self):
        self.stopping.set()
        self.pool.shutdown(wait=False, cancel_futures=True)
        for asset in self.library.list():
            if asset.get('blender', {}).get('status') in ('queued', 'running'):
                asset['blender'] = {'status': 'interrupted', 'message': 'Backend stopped. Retry preparation after restarting.'}
                self.library.save(asset)

    def get(self, key):
        if not isinstance(key, str) or len(key) != 32 or any(c not in '0123456789abcdef' for c in key):
            raise ValueError('Asset job not found.')
        with self.service.connect() as db:
            row = db.execute('SELECT data FROM asset_jobs WHERE id=?', (key,)).fetchone()
        if not row:
            raise ValueError('Asset job not found.')
        return json.loads(row[0])

    def save(self, job):
        with self.service.connect() as db:
            db.execute('INSERT OR REPLACE INTO asset_jobs VALUES (?,?)', (job['id'], json.dumps(job)))

    def update(self, key, **changes):
        with self.lock:
            job = self.get(key)
            job.update(changes)
            self.save(job)
        return job

    def submit(self, body):
        descriptor = prompt_request(body)
        token = local_settings()['ARC_LLM_API_KEY']
        if token and token in canonical(descriptor):
            raise ValueError('Remove the credential from this design. Nothing was saved.')
        with self.lock:
            jobs = self.list()
            match = next((j for j in jobs if j['prompt'] == descriptor and j['status'] != 'failed'), None)
            if match:
                return dict(match, reused=True)
            if any(j['status'] in ACTIVE | RECOVERABLE for j in jobs):
                raise ValueError('Finish or resolve the current asset dispatch before starting another.')
            # Preflight configuration only; no SSH calls block the HTTP request.
            if isinstance(self.transport, ArcTransport):
                self.transport.command('check')
                executable = local_settings()['BLENDER_EXECUTABLE']
                if not executable or not Path(executable).is_file():
                    raise ValueError('Configure the local Blender executable before starting an ARC generation.')
            job = {'id': uuid.uuid4().hex, 'prompt': descriptor, 'status': 'queued',
                   'message': 'Waiting for the ARC connection.', 'submission_started': False,
                   'created_at': datetime.now(UTC).isoformat()}
            self.save(job)
            self.pool.submit(self.run, job['id'])
        return job

    def resume(self, key):
        with self.lock:
            job = self.get(key)
            if job['status'] not in RECOVERABLE:
                raise ValueError('Only interrupted or uncertain jobs can be resumed.')
            if any(j['id'] != key and j['status'] in ACTIVE for j in self.list()):
                raise ValueError('Another asset job is active.')
            self.update(key, status='queued', message='Reconnecting to the same saved dispatch.')
            self.pool.submit(self.run, key)
        return self.get(key)

    def import_package(self, job, raw):
        if len(raw) > 245_000_000:
            raise ValueError('ARC result exceeds the automation package limit.')
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as outer:
                expected = {'binding.json', 'prompt.json', 'image-manifest.json', 'image-LICENSE.md', 'result.zip'}
                infos = outer.infolist()
                if set(outer.namelist()) != expected or len(infos) != len(expected) or sum(i.file_size for i in infos) > 245_000_000:
                    raise ValueError('Invalid automation package.')
                files = {n: outer.read(n) for n in expected}
            binding = json.loads(files['binding.json'])
            if binding != {'contract': 'fieldwork-automation-v1', 'dispatch': job['id'],
                           'files': {n: sha(files[n]) for n in expected-{'binding.json'}}}:
                raise ValueError('Automation result identity or checksums differ.')
            if json.loads(files['prompt.json']) != job['prompt']:
                raise ValueError('Returned result has a different description.')
            image = json.loads(files['image-manifest.json'])
            if image.get('settings') != job['prompt']['image_settings'] or image.get('prompt') != reference_prompt(job['prompt']) or image.get('seed') != job['prompt']['seed'] or image.get('stage') != 'reference_generated':
                raise ValueError('Reference generation provenance differs.')
            with zipfile.ZipFile(io.BytesIO(files['result.zip'])) as inner:
                info = inner.getinfo('reference.png')
                if info.file_size > 8_000_000:
                    raise ValueError('Invalid reference size.')
                png = inner.read('reference.png')
                shape_info = inner.getinfo('shape-manifest.json')
                if shape_info.file_size > 1_000_000:
                    raise ValueError('Invalid shape manifest size.')
                shape = json.loads(inner.read('shape-manifest.json'))
            if image.get('reference_sha256') != sha(png) or shape.get('job_id') != job['job_id']:
                raise ValueError('Reference or scheduler identity differs.')
            body = {k: job['prompt'][k] for k in ('family', 'name', 'description', 'dimensions_m', 'seed')}
            asset = self.library.create(dict(body, reference_png_base64=base64.b64encode(png).decode()))
            if not asset.get('result_revision'):
                asset = self.library.import_result(asset['id'], files['result.zip'])
            folder = self.library.directory/asset['id']
            for name in ('prompt.json', 'image-manifest.json', 'image-LICENSE.md', 'binding.json'):
                (folder/('automation-'+name)).write_bytes(files[name])
            return asset
        except (zipfile.BadZipFile, KeyError, TypeError, AttributeError, json.JSONDecodeError, UnicodeError, RuntimeError, NotImplementedError):
            raise ValueError('ARC returned an invalid automation package.') from None

    def run(self, key):
        try:
            job = self.update(key, status='connecting', message='Checking the ARC SSH worker.')
            self.transport.check()
            if self.stopping.is_set():
                self.update(key, status='interrupted', message='Backend stopped before submission. Resume after restarting.')
                return
            if not job.get('submission_started'):
                self.update(key, status='submitting', submission_started=True, message='Submitting one Slurm job.')
                remote = self.transport.call('submit', key, job['prompt'])
                if remote.get('job_id'):
                    self.update(key, job_id=remote['job_id'])
            deadline = time.monotonic()+3*60*60
            while time.monotonic() < deadline and not self.stopping.is_set():
                remote = self.transport.call('status', key)
                state = remote.get('state', '')
                if state in ('SUBMISSION_UNKNOWN', 'NOT_FOUND'):
                    self.update(key, status='submission_unknown', message='Submission is uncertain. Resume to query the same dispatch; no automatic resubmission.')
                    return
                if remote.get('job_id'):
                    if self.get(key).get('job_id') not in (None, remote['job_id']):
                        raise ValueError('Scheduler identity changed unexpectedly.')
                    self.update(key, job_id=remote['job_id'])
                self.update(key, status='remote', scheduler_state=state, phase=remote.get('phase', ''),
                            message='ARC: '+state+' · '+remote.get('phase', ''))
                if state == 'COMPLETED':
                    if remote.get('exit_code') != '0:0' or not remote.get('result_ready'):
                        raise ValueError('Slurm finished without a successful complete result package.')
                    break
                if state in ('FAILED', 'CANCELLED', 'TIMEOUT', 'OUT_OF_MEMORY', 'NODE_FAIL', 'PREEMPTED', 'BOOT_FAIL'):
                    self.update(key, status='failed', message='ARC job '+state+'. Inspect its saved ARC logs before a new attempt.')
                    return
                self.stopping.wait(self.poll_seconds)
            else:
                self.update(key, status='interrupted', message='Monitoring stopped. Resume this saved ARC job; do not submit again.')
                return
            self.update(key, status='importing', message='Retrieving and validating the actual generated model.')
            asset = self.import_package(self.get(key), self.transport.call('download', key))
            if self.stopping.is_set():
                self.update(key, status='needs_preparation', asset_id=asset['id'], message='Generated model saved. Prepare it after restarting the backend.')
                return
            self.update(key, status='preparing', asset_id=asset['id'], message='Blender MCP is preparing cleanup, collisions and Unreal export.')
            if asset.get('blender', {}).get('status') != 'complete':
                self.library.prepare(asset['id'])
            deadline = time.monotonic()+3600
            while time.monotonic() < deadline and not self.stopping.is_set():
                prepared = self.library.get(asset['id']).get('blender', {})
                if prepared.get('status') == 'complete':
                    self.update(key, status='review_ready', message='Blender and Unreal package ready for visual review; engine import/cooking remains unverified.')
                    return
                if prepared.get('status') in ('failed', 'interrupted'):
                    self.update(key, status='needs_preparation', message='Generated model saved. Retry Blender preparation on its design card.')
                    return
                self.stopping.wait(max(.05, min(self.poll_seconds, 2)))
            self.update(key, status='needs_preparation', message='Model saved; Blender preparation can be inspected on its card.')
        except ArcConnectionError as exc:
            job = self.get(key)
            self.update(key, status='connection_lost' if job.get('submission_started') else 'failed',
                        message=str(exc)[:500])
        except (OSError, ValueError) as exc:
            # All transport errors have bounded user-facing messages; no raw SSH stderr is returned.
            job = self.get(key)
            uncertain = job.get('submission_started') and job['status'] in ('connecting', 'submitting', 'remote')
            self.update(key, status='connection_lost' if uncertain else 'failed', message=str(exc)[:500])
