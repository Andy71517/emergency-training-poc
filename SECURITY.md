# Security policy

Only current `main` is maintained. FIELDWORK is a local single-user POC with hosted
model requests, SSH/Slurm transport and native Blender/Unreal workers. It has no
application login or production multi-user security model; keep it on loopback.

Report issues privately to the repository owner when they could expose credentials,
private files or access. Do not place secrets or exploit details in public issues.
Useful reports include path/command injection, package/resource validation bypass,
credential leakage, duplicate GPU submission, forged/stale evidence and dependency risks.

Current guardrails and remaining limitations are described in
[security overview](docs/security/README.md) and [threat model](docs/security/poc-threat-model.md).
Never disable TLS/SSH host verification as a workaround. Passwords, Duo, SSH private
keys and passphrases stay in user-controlled authentication tools, not chat or the app.

There is no production authentication/authorization, public TLS deployment, role
model, audited data-retention policy or clinical-data governance. Institution-approved
hosting/delegation, sensing and real training data need separate design/review.
