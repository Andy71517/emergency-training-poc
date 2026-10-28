# Local POC threat model

Reviewed against the current studio, ARC transport and native workers. This is an
unauthenticated single-user loopback app, not a production service.

| Boundary/risk | Current control | Remaining limit |
| --- | --- | --- |
| Client claims scenario truth | Backend applies ordered actions and explicit rules; logs/reviews derive from saved state | No authenticated users/roles |
| Invalid/large input | Bounded schemas, safe IDs, sequence/duplicate/session limits | No production rate limiting or distributed quotas |
| Foreign-origin actions | Studio mutation routes reject foreign origins | Origin checks are not authentication or complete browser/network isolation |
| Model-generated commands | Plans parsed/validated as data; fixed worker actions | Semantic compliance and quality still need inspection |
| SSH command/path injection | Fixed RPC, validated backend config/dispatch, no browser shell arguments | Runs with the user's existing account permissions |
| Untrusted remote host | Strict host verification and noninteractive agent-based access | User must establish trusted host/key setup; no bypass |
| Lost submission acknowledgment | Local/remote journals, Slurm comment recovery, no blind resubmit | Unknown evidence can require manual investigation |
| ZIP/resource abuse | Identity/hash/name/size checks and embedded GLB resource requirements | Parser/native dependencies and complex geometry remain attack surfaces |
| Blender execution | Scoped MCP IDs, fixed scripts, isolated processes and timeouts | Native application/library vulnerabilities are not eliminated |
| Engine evidence mismatch | Job/room/run hashes and restricted local bridge actions | Client/engine reports are observations, not independently calibrated truth |
| Secret/data leakage | Private ignored config, filtered child env, sanitized transport errors | Raw native logs and provider-bound prompts need human data hygiene |
| Destructive cleanup | Recoverable batch Trash; fixed generated-output locations | Manual filesystem actions and external editor changes need care |

Before hosting, design authentication/authorization, TLS, quotas, institutional ARC
service access, job ownership, worker isolation, dependency/security monitoring,
retention and auditing. Sensing and clinical data add separate consent/validation
requirements. [Security overview](README.md), [data handling](logging-and-data-handling.md).
