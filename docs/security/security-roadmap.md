# Security roadmap

The current local baseline includes session input/sequence limits, scoped studio
artifacts, bounded packages, foreign-origin mutation checks, verified fixed SSH
RPC and bounded Blender MCP/native workers. See the [threat model](poc-threat-model.md).
These controls do not make a hosted multi-user service.

## Strengthen local evidence

- Continue recovery/injection/package/worker regression checks.
- Review dependencies, native parser boundaries and sanitized diagnostics.
- Define practical manual retention/backups for growing local/ARC outputs.
- Keep fixture/live/unverified evidence labels clear and credentials user-controlled.

## Before network hosting or delegated ARC access

- Institution-approved worker identity, job ownership, delegation and quotas.
- Application authentication, authorization/roles and per-user artifact boundaries.
- TLS, network restrictions, isolated workers, secret management and audit trails.
- Rate limits, storage/compute budgets and operational failure/recovery policy.
- Retention, export/deletion and incident reporting.

CS Launch is a future target. A local personal SSH agent is not a hosted service
credential architecture. The existing editor bridge is not the future authenticated
trainee WebSocket client.

## Before real training or sensing data

Agree on consent, privacy, permitted data, retention/access, confidence handling,
domain validation and independent evaluation with qualified reviewers. Keep real
patient/trainee/operational data out of this POC until those decisions exist.
