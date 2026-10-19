"""Local persistent jobs; credentials never enter job records or browser responses."""
import hashlib
import json
import os
import sqlite3
import threading
import unicodedata
import urllib.error
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from arc.scripts.check_arc_network import describe_connection_error
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

    def records(self):
        with self.connect() as db:
            rows = db.execute('SELECT data FROM jobs ORDER BY rowid DESC').fetchall()
        return [json.loads(row[0]) for row in rows]

    def list(self):
        return [j for j in self.records() if not j.get('trashed_at')][:100]

    def trash_list(self):
        return [j for j in self.records() if j.get('trashed_at')][:100]

    @staticmethod
    def request_key(prompt,count,seed,model):
        prompt=unicodedata.normalize('NFC',prompt.replace('\r\n','\n').strip())
        value={'prompt':prompt,'count':count,'seed':seed,'model':model,'contract':'studio-plan-v1'}
        return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()

    def find_match(self,prompt,count,seed,model=None):
        model=model or settings()[1]
        key=self.request_key(prompt,count,seed,model)
        candidates=[j for j in self.records() if not j.get('trashed_at')
            and j['status'] in ('queued','planning','building','review_ready')
            and (j['status']!='review_ready' or (self.directory/j['id']/'manifest.json').is_file())
            and self.request_key(j['prompt'],j['count'],j['seed'],j['model'])==key]
        return next((j for j in candidates if j['status']!='review_ready'),candidates[0] if candidates else None)

    @staticmethod
    def working(job):
        return job['status'] in ('queued','planning','building') or any(
            state.get('status') in ('queued','running') for state in job.get('pipeline',{}).values())

    def trash(self,job_id):
        with self.lock:
            job=self.get(job_id)
            if self.working(job):
                raise ValueError('This batch is still working. Wait for it to finish before deleting it.')
            job['trashed_at']=datetime.now(UTC).isoformat()
            self.save(job)
        return job

    def restore(self,job_id):
        with self.lock:
            job=self.get(job_id)
            job.pop('trashed_at',None)
            self.save(job)
        return job

    def submit(self, prompt, count, seed, force_new=False):
        token, model = settings()
        if len(prompt.strip())<10:
            raise ValueError('Describe the scenario in at least ten non-blank characters.')
        if token and token in prompt:
            raise ValueError('The prompt contains a credential. Remove it; nothing was saved.')
        with self.lock:
            if not force_new:
                existing=self.find_match(prompt,count,seed,model)
                if existing:
                    # Reopen even an older match in the bounded Recent batches list.
                    if existing['status']=='review_ready':
                        self.save(existing)
                    return dict(existing,reused=True)
            if not token:
                raise ValueError('Configure ARC_LLM_API_KEY in backend/.env, then try again.')
            if sum(j['status'] in ('queued','planning','building') for j in self.list()) >= 4:
                raise ValueError('Four jobs are already active. Wait for a job to finish.')
            job = {'id':uuid.uuid4().hex, 'prompt':prompt,'count':count,'seed':seed,
                   'model':model,'status':'queued','created_at':datetime.now(UTC).isoformat(),
                   'error':None,'plan':None,'scenes':[],'stages':{'planning':'queued','blender':'not_connected','unreal':'not_connected'},
                   'request_key':self.request_key(prompt,count,seed,model)}
            self.save(job)
            self.pool.submit(self.run, job['id'], token)
        return dict(job,reused=False)

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
        except (urllib.error.URLError, TimeoutError) as exc:
            job.update(status='failed', error=describe_connection_error(exc))
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
                   scenes=[], pipeline={}, stages={'planning':'building','blender':'not_started','unreal':'not_started'},
                   created_at=datetime.now(UTC).isoformat(), replay_of=job_id)
        job.pop('trashed_at',None)
        job.pop('completed_at',None)
        job['request_key']=self.request_key(job['prompt'],job['count'],seed,job['model'])
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
