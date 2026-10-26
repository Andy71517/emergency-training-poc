"""Offline Slurm RPC tests. No scheduler or model execution is claimed."""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('remote_control', SCRIPTS/'remote_asset_control.py')
remote = importlib.util.module_from_spec(spec)
spec.loader.exec_module(remote)


def descriptor():
    return remote.validate_prompt(__import__('automation_contract').prompt_request(
        {'family': 'couch', 'name': 'Offline fixture couch', 'description': 'Two cushions and four legs.',
         'dimensions_m': [1.8, .85, .85], 'seed': 42}))


@pytest.fixture(autouse=True)
def scheduler_environment(monkeypatch):
    for key in ('ARC_ACCOUNT', 'ARC_GPU_PARTITION', 'ARC_GPU_QOS', 'USER'):
        monkeypatch.setenv(key, 'offline-fixture')
    if os.name == 'nt':
        # File-lock semantics are native to the Linux ARC host, not Windows.
        # Exercise the journal behavior here; CI on Linux uses real flock.
        monkeypatch.setitem(sys.modules, 'fcntl', SimpleNamespace(LOCK_EX=1, flock=lambda *a: None))


def test_exact_dispatch_is_submitted_once(tmp_path, monkeypatch):
    calls = []
    def run(command, **kwargs):
        calls.append(command)
        assert command[:2] == ['sbatch', '--parsable']
        assert kwargs['env']['FIELDWORK_DISPATCH'] == 'a'*32
        return subprocess.CompletedProcess(command, 0, '12345\n', '')
    monkeypatch.setattr(remote.subprocess, 'run', run)
    first = remote.submit(tmp_path, 'a'*32, descriptor())
    assert remote.submit(tmp_path, 'a'*32, descriptor()) == first
    assert len(calls) == 1
    assert first['job_id'] == '12345'
    changed = dict(descriptor(), seed=43)
    with pytest.raises(ValueError, match='different prompt'):
        remote.submit(tmp_path, 'a'*32, changed)


def test_lost_ack_is_recovered_from_scheduler_comment_without_resubmission(tmp_path, monkeypatch):
    folder = tmp_path/('b'*32)
    folder.mkdir()
    (folder/'submitting').write_text('ack lost')
    calls = []
    def run(command, **kwargs):
        calls.append(command[0])
        return subprocess.CompletedProcess(command, 0, '789|fieldwork:'+'b'*32+'\n', '')
    monkeypatch.setattr(remote.subprocess, 'run', run)
    result = remote.submit(tmp_path, 'b'*32, descriptor())
    assert result['job_id'] == '789'
    assert 'sbatch' not in calls


def test_absent_accounting_is_unknown_not_another_submission(tmp_path, monkeypatch):
    folder = tmp_path/('c'*32)
    folder.mkdir()
    (folder/'submitting').write_text('ack lost')
    calls = []
    def run(command, **kwargs):
        calls.append(command[0])
        return subprocess.CompletedProcess(command, 0, '', '')
    monkeypatch.setattr(remote.subprocess, 'run', run)
    assert remote.submit(tmp_path, 'c'*32, descriptor())['state'] == 'SUBMISSION_UNKNOWN'
    assert 'sbatch' not in calls


def test_status_binds_exact_job_and_requires_result_package(tmp_path, monkeypatch):
    folder = tmp_path/('d'*32)
    folder.mkdir()
    (folder/'submitted.json').write_text(json.dumps({'dispatch': 'd'*32, 'job_id': '100'}))
    monkeypatch.setattr(remote.subprocess, 'run', lambda command, **kwargs:
                        subprocess.CompletedProcess(command, 0, '100|COMPLETED|0:0\n', ''))
    status = remote.status(tmp_path, 'd'*32)
    assert status['state'] == 'COMPLETED' and status['result_ready'] is False
    (folder/'automation-result.zip').write_bytes(b'offline fixture')
    assert remote.status(tmp_path, 'd'*32)['result_ready'] is True
    with pytest.raises(ValueError):
        remote.folder_for(tmp_path, '../elsewhere')
