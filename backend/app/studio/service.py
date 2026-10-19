"""Local persistent jobs; credentials never enter job records or browser responses."""
import json
import os
import sqlite3
import threading
import urllib.error
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from arc.scripts.check_scenario_planner_access import safe_error_detail
from arc.scripts.generate_scenario_batch import ask_model, write_package

REPO = Path(__file__).resolve().parents[3]


def local_settings():
    values = {}
    path = REPO/'backend'/'.env'
    if path.is_file():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            if '=' not in line or line.lstrip().startswith('#'):
                continue
            key, value = line.split('=', 1)
            if key.strip() in ('ARC_LLM_API_KEY', 'ARC_LLM_MODEL', 'BLENDER_EXECUTABLE', 'CHAIR_BLEND'):
                values[key.strip()] = value.strip().strip('\"\'')
    return {key: os.environ.get(key, values.get(key, default)) for key, default in (
        ('ARC_LLM_API_KEY', ''), ('ARC_LLM_MODEL', 'gpt-oss-120b'),
        ('BLENDER_EXECUTABLE', ''), ('CHAIR_BLEND', ''))}


def settings():
    values = local_settings()
    return values['ARC_LLM_API_KEY'], values['ARC_LLM_MODEL']



class SceneBatchService:
    def __init__(self, directory: Path, planner=ask_model):
        self.directory = directory.resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.db = self.directory/'jobs.sqlite3'
        self.planner = planner
        self.lock = threading.Lock()
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix='arc-planner')
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, data TEXT NOT NULL)')
            rows = db.execute('SELECT id,data FROM jobs').fetchall()
            for job_id, data in rows:
                job = json.loads(data)
                if job['status'] in ('queued','planning','building'):
                    job.update(status='interrupted', error='Backend restarted. Submit again; no automatic model retry.')
                    db.execute('UPDATE jobs SET data=? WHERE id=?', (json.dumps(job),job_id))

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.db, timeout=10)
        try:
            with db:
                yield db
        finally:
            db.close()

    def save(self, job):
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO jobs VALUES (?,?)',(job['id'],json.dumps(job)))

    def get(self, job_id):
        with self.connect() as db:
            row = db.execute('SELECT data FROM jobs WHERE id=?',(job_id,)).fetchone()
        if row is None:
            raise KeyError(job_id)
        return json.loads(row[0])

    def list(self):
        with self.connect() as db:
            rows = db.execute('SELECT data FROM jobs ORDER BY rowid DESC LIMIT 100').fetchall()
        return [json.loads(row[0]) for row in rows]

    def submit(self, prompt, count, seed):
        token, model = settings()
        if not token:
            raise ValueError('Configure ARC_LLM_API_KEY in backend/.env, then try again.')
        if token in prompt:
            raise ValueError('The prompt contains a credential. Remove it; nothing was saved.')
        with self.lock:
            if sum(j['status'] in ('queued','planning','building') for j in self.list()) >= 4:
                raise ValueError('Four jobs are already active. Wait for a job to finish.')
            job = {'id':uuid.uuid4().hex, 'prompt':prompt,'count':count,'seed':seed,
                   'model':model,'status':'queued','created_at':datetime.now(UTC).isoformat(),
                   'error':None,'plan':None,'scenes':[],'stages':{'planning':'queued','blender':'not_connected','unreal':'not_connected'}}
            self.save(job)
            self.pool.submit(self.run, job['id'], token)
        return job

    def run(self, job_id, token):
        job = self.get(job_id)
        try:
            job['status']='planning'
            self.save(job)
            plan, source = self.planner(job['prompt'], job['count'], job['model'], token=token)
            job.update(status='building',plan=plan)
            self.save(job)
            output = write_package(self.directory/job_id, plan, source, job['seed'],job['prompt'])
            scenes = [json.loads(p.read_text()) for p in sorted(output.glob('room_*.json'))]
            job.update(status='review_ready',scenes=scenes,completed_at=datetime.now(UTC).isoformat(),error=None)
            job['stages']['planning']='complete'
        except (urllib.error.URLError, TimeoutError):
            job.update(status='failed', error='ARC connection failed or timed out. Check the VT VPN and internet connection, then use Test ARC connection. No automatic retry was made.')
            job['stages']['planning']='failed'
        except ValueError as exc:
            detail = safe_error_detail(json.dumps({'message':str(exc)}).encode(), token)
            job.update(status='failed', error=detail)
            job['stages']['planning']='failed'
        except (KeyError, IndexError, TypeError):
            job.update(status='failed', error='ARC returned an unexpected response format. Test the connection, then retry the request.')
            job['stages']['planning']='failed'
        except Exception:  # noqa: BLE001 - worker boundary must persist a failure without leaking secrets
            # Never expose exception bodies, network payloads or credentials via API/logs.
            job.update(status='failed',error='Generation failed unexpectedly. Check the ARC connection and retry; no substitute plan was generated.')
            job['stages']['planning']='failed'
        self.save(job)


    def replay(self, job_id, seed):
        old = self.get(job_id)
        if old.get('plan') is None:
            raise ValueError('This job has no saved validated plan. Edit the brief and generate again.')
        from arc.scripts.generate_scenario_batch import validate_plan
        plan = validate_plan(old['plan'])
        job = dict(old, id=uuid.uuid4().hex, seed=seed, status='building', error=None,
                   scenes=[], stages={'planning':'building','blender':'not_started','unreal':'not_started'},
                   created_at=datetime.now(UTC).isoformat(), replay_of=job_id)
        with self.lock:
            if sum(j['status'] in ('queued','planning','building') for j in self.list()) >= 4:
                raise ValueError('Four jobs are active. Wait for a job to finish.')
            self.save(job)
            self.pool.submit(self.run_replay, job, plan)
        return job

    def run_replay(self, job, plan):
        try:
            out = write_package(self.directory/job['id'], plan,
                {'provider':'saved_plan_replay','source_job':job['replay_of']}, job['seed'], job['prompt'])
            scenes = [json.loads(p.read_text(encoding='utf-8')) for p in sorted(out.glob('room_*.json'))]
            job.update(status='review_ready',scenes=scenes)
            job['stages']['planning']='complete'
        except Exception:  # noqa: BLE001 - persist replay worker failures
            job.update(status='failed',error='The saved plan cannot fit this layout. Edit the brief and generate again.')
            job['stages']['planning']='failed'
        self.save(job)
