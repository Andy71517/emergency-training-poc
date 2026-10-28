# Backend and ARC tests

From the repository root after installing `.[dev]`:

```powershell
python -m pytest -q backend/tests arc/tests
```

Default `pytest` selects backend tests only. The last implementation checkpoint
passed 138 combined tests. See [CI](../../docs/development/ci.md) for exact checks
and Windows Git Bash setup.

Coverage includes deterministic state/sequence/rule/log/replay behavior; API and
WebSocket contracts; studio planning/layout/reuse/Trash and worker evidence;
asset request/result hashes and bounded imports; SSH dispatch uncertainty and
same-job recovery; real MCP handshake/tool schemas; preparation failures and stale
workers; recording protocols; generic Unreal package preflight.

Model/SSH/editor transports are mocked where appropriate. A test that simulates
Slurm or an editor does not prove remote generation or real engine physics. Native
Blender/CoACD fixture validation and user-confirmed engine evidence are recorded
separately in [current status](../../docs/current-status.md).
