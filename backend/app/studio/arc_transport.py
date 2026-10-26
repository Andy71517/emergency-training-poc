"""Backend-owned, fixed SSH RPC. No passwords, shell text or paths from the browser."""
import json
import os
import re
import shlex
import subprocess

from backend.app.studio.service import local_settings

LIMIT = 245_000_000


class ArcConnectionError(ValueError):
    """A transport failure which can be resumed without a new scheduler job."""


class ArcTransport:
    def __init__(self, config=None):
        self.config = config or local_settings()

    def command(self, action, dispatch=None):
        target = self.config.get('ARC_SSH_TARGET', '')
        repo = self.config.get('ARC_REMOTE_REPO', '')
        if not re.fullmatch(r'(?:[A-Za-z0-9_.-]+@)?[A-Za-z0-9][A-Za-z0-9_.-]{0,200}', target):
            raise ValueError('Set ARC_SSH_TARGET in backend/.env to your verified SSH host or alias.')
        if not re.fullmatch(r'/[A-Za-z0-9_./-]+', repo) or '..' in repo.split('/'):
            raise ValueError('Set ARC_REMOTE_REPO to the absolute ARC checkout path in backend/.env.')
        if action not in ('check', 'submit', 'status', 'download'):
            raise ValueError('Unsupported remote action.')
        if action != 'check' and not re.fullmatch('[a-f0-9]{32}', dispatch or ''):
            raise ValueError('Invalid dispatch.')
        remote = 'cd ' + shlex.quote(repo) + ' && bash arc/scripts/remote_asset_control.sh ' + action
        if dispatch:
            remote += ' ' + dispatch
        return ['ssh', '-T', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
                '-o', 'ConnectTimeout=10', '-o', 'ServerAliveInterval=15',
                '-o', 'ServerAliveCountMax=2', target, remote]

    def call(self, action, dispatch=None, value=None):
        command = self.command(action, dispatch)
        raw = json.dumps(value).encode() if value is not None else None
        env = {k: v for k, v in os.environ.items() if k not in ('ARC_LLM_API_KEY', 'OPENAI_API_KEY', 'HF_TOKEN')}
        # Download is streamed with an explicit cap; stderr never enters a browser response.
        try:
            if action == 'download':
                with subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                      stderr=subprocess.DEVNULL, env=env) as process:
                    import threading
                    timer = threading.Timer(300, process.kill)
                    timer.start()
                    try:
                        result = bytearray()
                        while chunk := process.stdout.read(1024*1024):
                            result.extend(chunk)
                            if len(result) > LIMIT:
                                process.kill()
                                raise ValueError('Returned ARC package exceeds the transport limit.')
                        if process.wait(timeout=10):
                            raise ArcConnectionError('ARC result transfer failed. Reconnect and resume; do not resubmit.')
                        return bytes(result)
                    finally:
                        timer.cancel()
            result = subprocess.run(command, input=raw, capture_output=True, timeout=120, check=False, env=env)
            if result.returncode:
                raise ArcConnectionError('ARC connection failed. Check VPN, trusted host, unlocked SSH agent, '
                                 'remote checkout and arc/.env. Use the setup runbook; no password is collected here.')
            if len(result.stdout) > 65536:
                raise ValueError('Unexpected ARC control response size.')
            value = json.loads(result.stdout)
            if not isinstance(value, dict):
                raise ValueError('Unexpected ARC control response.')  # noqa: TRY004 - HTTP boundary uses ValueError
            if dispatch and value.get('dispatch') != dispatch:
                raise ValueError('ARC returned a different dispatch identity.')
            return value
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
            raise ArcConnectionError('ARC connection interrupted. Check SSH/VPN and resume this saved job.') from None

    def check(self):
        result = self.call('check')
        if result.get('version') != 'fieldwork-automation-v1' or result.get('runtimes_ready') is not True:
            raise ValueError('Update the ARC checkout and verify its existing shape/texture runtimes first.')
        return {'ok': True, 'message': 'SSH worker connected; shape and paint runtime markers found. '
                'The new image/GPU lane still needs its first actual run.'}
