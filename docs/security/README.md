# Security overview

This folder explains the security thinking for the POC.

The short version:

The backend should be the source of truth. A client can ask for actions, but it should not decide scenario state, validation results, replay results, or final outcomes.

Right now this is still a local demo. The goal is not production security yet. The goal is to make the trust boundary clear and block obvious bad inputs early.

## Current security baseline

The backend now does a few starter checks:

- rejects unexpected message fields
- limits IDs to simple safe characters
- rejects path-like or weird scenario IDs
- keeps payloads small and JSON-shaped
- checks session ID consistency between the URL, envelope, and event
- checks ordered sequence numbers
- rejects duplicate event IDs
- limits active sessions
- limits actions per session
- keeps logs in `logs/sessions/`

## What this does not solve yet

This does not add:

- authentication
- authorization
- TLS
- real rate limiting
- multi-user access control
- secrets management
- production deployment security

That is okay for this stage. This is a POC security floor, not the final security ceiling.

## Files in this folder

- `poc-threat-model.md`: what could go wrong in the current local demo
- `client-trust-boundary.md`: what the backend should and should not trust from clients
- `logging-and-data-handling.md`: how local logs should be treated
- `websocket-error-codes.md`: current client-facing WebSocket error codes
- `demo-day-checklist.md`: quick checklist before presenting the demo
- `security-roadmap.md`: how security should grow as the project grows
