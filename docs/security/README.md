# Security overview

FIELDWORK is a local single-user POC with real hosted requests, SSH job transport
and native workers. Keep it on loopback. Input guardrails and fixed tools do not
replace authentication, multi-user authorization or production deployment controls.

## Current boundaries

- Session actions use bounded schemas/IDs, sequence checks, duplicate rejection and
  active-session/action limits. The backend owns state, findings, logs and review.
- Studio actions reject foreign origins, constrain requests/uploads and derive
  allowlisted artifact paths. SQLite and saved outputs stay under ignored local logs.
- Plans are validated data; model text is never run as Python/shell code.
- SSH RPC uses configured backend paths, BatchMode and strict host verification.
  Dispatch journals and scheduler evidence support recovery without blind resubmission.
- Blender MCP exposes two scoped fixed tools over stdio; it is not a public socket
  or arbitrary-code Blender add-on. Native process timeouts and output checks bound work.
- Package identities/hashes, embedded resource restrictions and expanded-size limits
  constrain imports. These checks do not establish visual quality or training validity.
- Hosted keys stay backend-only and are excluded from worker environments. Passwords,
  Duo, SSH private keys and passphrases stay in user-controlled authentication tools.

## Still outside this boundary

There is no application login, role-based access, production rate limiting,
multi-user quota/authorization, public TLS deployment, production retention or
clinical data governance. The remote SSH account's actual permissions remain the
user's permissions; fixed commands are not an institutional service-access agreement.
CS Launch deployment needs separate security design and approval.

## Guides

- [Threat model](poc-threat-model.md)
- [Client trust](client-trust-boundary.md)
- [Data and logs](logging-and-data-handling.md)
- [WebSocket errors](websocket-error-codes.md)
- [Demo checklist](demo-day-checklist.md)
- [Security roadmap](security-roadmap.md)
- [Asset connection setup](../asset-automation-runbook.md)
- [Current status](../current-status.md)
