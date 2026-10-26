"""Small login-node RPC: journal dispatches, query Slurm, retrieve bounded results."""
import argparse
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

from automation_contract import canonical, sha, validate_prompt

VERSION = 'fieldwork-automation-v1'
TERMINAL = {'COMPLETED', 'FAILED', 'CANCELLED', 'TIMEOUT', 'OUT_OF_MEMORY', 'NODE_FAIL', 'PREEMPTED', 'BOOT_FAIL'}


def write_json(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(canonical(value)+'\n')
    temp.replace(path)


def folder_for(root, dispatch):
    if not re.fullmatch('[a-f0-9]{32}', dispatch):
        raise ValueError('Invalid dispatch ID.')
    folder = (root / dispatch).resolve()
    if folder.parent != root.resolve():
        raise ValueError('Invalid dispatch folder.')
    return folder


def recover_job(dispatch):
    """Never interpret absent accounting evidence as permission to submit twice."""
    tag = 'fieldwork:' + dispatch
    commands = [
        ['squeue', '-h', '-u', os.environ.get('USER', ''), '-o', '%i|%k'],
        ['sacct', '-X', '-n', '-P', '-u', os.environ.get('USER', ''), '-S', 'now-7days',
         '--format=JobIDRaw,Comment'],
    ]
    found = set()
    for command in commands:
        result = subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)
        if result.returncode:
            continue
        for line in result.stdout.splitlines():
            parts = line.strip().split('|')
            if len(parts) >= 2 and parts[1] == tag and parts[0].isdigit():
                found.add(parts[0])
    if len(found) > 1:
        raise ValueError('More than one scheduler job matches this dispatch; inspect ARC before continuing.')
    return next(iter(found), None)


def submit(root, dispatch, value):
    import fcntl

    value = validate_prompt(value)
    folder = folder_for(root, dispatch)
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / 'dispatch.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        prompt_file = folder / 'prompt.json'
        if prompt_file.is_file() and json.loads(prompt_file.read_bytes()) != value:
            raise ValueError('Dispatch is already bound to a different prompt.')
        write_json(prompt_file, value)
        journal = folder / 'submitted.json'
        if journal.is_file():
            return json.loads(journal.read_bytes())
        marker = folder / 'submitting'
        if marker.exists():
            job = recover_job(dispatch)
            if not job:
                return {'dispatch': dispatch, 'state': 'SUBMISSION_UNKNOWN'}
        else:
            marker.write_text('Submission may have reached Slurm. Recover before any retry.\n')
            command = ['sbatch', '--parsable', '--comment=fieldwork:'+dispatch,
                       '--account='+os.environ['ARC_ACCOUNT'], '--partition='+os.environ['ARC_GPU_PARTITION'],
                       '--qos='+os.environ['ARC_GPU_QOS'], 'arc/jobs/generate_automated_furniture.sbatch']
            env = dict(os.environ, FIELDWORK_DISPATCH=dispatch)
            result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=45, check=False)
            if result.returncode or not re.fullmatch(r'\d+(;[A-Za-z0-9_-]+)?\s*', result.stdout):
                return {'dispatch': dispatch, 'state': 'SUBMISSION_UNKNOWN'}
            job = result.stdout.strip().split(';')[0]
        record = {'dispatch': dispatch, 'job_id': job, 'state': 'PENDING'}
        write_json(journal, record)
        return record


def status(root, dispatch):
    folder = folder_for(root, dispatch)
    journal = folder / 'submitted.json'
    if not journal.is_file():
        job = recover_job(dispatch) if (folder / 'submitting').is_file() else None
        if not job:
            return {'dispatch': dispatch, 'state': 'SUBMISSION_UNKNOWN' if (folder/'submitting').exists() else 'NOT_FOUND'}
        write_json(journal, {'dispatch': dispatch, 'job_id': job})
    record = json.loads(journal.read_bytes())
    job = record['job_id']
    if not re.fullmatch(r'\d+', job):
        raise ValueError('Invalid saved scheduler identity.')
    result = subprocess.run(['sacct', '-X', '-n', '-P', '-j', job, '--format=JobIDRaw,State,ExitCode'],
                            capture_output=True, text=True, timeout=30, check=False)
    state, exit_code = 'ACCOUNTING_PENDING', ''
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            parts = line.strip().split('|')
            if len(parts) >= 3 and parts[0] == job:
                state, exit_code = parts[1].split()[0].split('+')[0], parts[2]
    if state == 'ACCOUNTING_PENDING':
        queued = subprocess.run(['squeue', '-h', '-j', job, '-o', '%T'],
                                capture_output=True, text=True, timeout=30, check=False)
        if queued.returncode == 0 and queued.stdout.strip():
            state = queued.stdout.strip().splitlines()[0]
    phase = (folder/'phase').read_text().strip() if (folder/'phase').is_file() else ''
    return dict(record, state=state, exit_code=exit_code,
                phase=phase if phase in ('image', 'shape', 'texture', 'packaged') else '',
                result_ready=(folder/'automation-result.zip').is_file())


def package(root, dispatch):
    folder = folder_for(root, dispatch)
    files = {'prompt.json': folder/'prompt.json', 'image-manifest.json': folder/'request/image-manifest.json',
             'image-LICENSE.md': folder/'request/image-LICENSE.md', 'result.zip': folder/'result.zip'}
    binding = {'contract': VERSION, 'dispatch': dispatch,
               'files': {name: sha(path.read_bytes()) for name, path in files.items()}}
    target = folder/'automation-result.tmp'
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_STORED) as archive:
        for name, path in files.items():
            archive.write(path, name)
        archive.writestr('binding.json', canonical(binding))
    if target.stat().st_size > 245_000_000:
        raise ValueError('Automation result exceeds the transport limit.')
    target.replace(folder/'automation-result.zip')


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('check', 'submit', 'status', 'download', 'package'))
    parser.add_argument('dispatch', nargs='?')
    parser.add_argument('--root', type=Path)
    args = parser.parse_args()
    root = args.root or Path(os.environ['ARC_HUNYUAN_ROOT'])/'automation'
    if args.action == 'check':
        runtime = root.parent
        ready = all((runtime/'metadata'/name).is_file() for name in ('runtime-ready.env', 'texture-ready.env'))
        print(canonical({'version': VERSION, 'runtimes_ready': ready}))
    elif args.action == 'submit':
        for name in ('runtime-ready.env', 'texture-ready.env'):
            if not (root.parent/'metadata'/name).is_file():
                raise ValueError('Verify the existing shape and paint runtimes first.')
        Path('arc/results').mkdir(exist_ok=True)
        raw = sys.stdin.buffer.read(65537)
        if len(raw) > 65536:
            raise ValueError('Prompt descriptor too large.')
        print(canonical(submit(root, args.dispatch, json.loads(raw))))
    elif args.action == 'status':
        print(canonical(status(root, args.dispatch)))
    elif args.action == 'package':
        package(root, args.dispatch)
    else:
        path = folder_for(root, args.dispatch)/'automation-result.zip'
        if not path.is_file() or path.stat().st_size > 245_000_000:
            raise ValueError('No bounded result package available.')
        with path.open('rb') as source:
            while chunk := source.read(1024*1024):
                sys.stdout.buffer.write(chunk)


if __name__ == '__main__':
    main()
