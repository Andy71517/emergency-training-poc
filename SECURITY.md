# Security policy for this POC

This repo is a local proof of concept, not a production system.

That means the security goal right now is modest:

Keep the demo safe enough to run locally, make trust boundaries clear, and avoid building habits that would become dangerous later.

## Supported version

Only the current `main` branch is maintained.

## What to report

If you find a security issue, open an issue or contact the repo owner directly.

Useful things to report:

- ways to write logs outside `logs/sessions/`
- ways to bypass message validation
- ways to make replay produce a different result from the original run
- places where client input is treated as trusted truth
- dependency or packaging risks

## Current security limits

This POC does not currently include:

- authentication
- authorization
- TLS setup
- user accounts
- role-based access
- cloud deployment security
- production log retention
- sensor security
- Unreal client hardening

Those belong in later slices, after the local backend loop is stable.

