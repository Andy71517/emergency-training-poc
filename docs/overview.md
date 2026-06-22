# POC Overview

This POC isolates one question: can a trainee action pass through a deterministic backend and produce a validated, logged state message suitable for a future client?

The backend will eventually accept a manual or scripted action, load the current session and scenario, apply exactly one transition, run scenario-specific conformance rules, persist an append-only JSONL record, and return the resulting state. The same input state and ordered events must produce the same output.

Sprint 0 contains contracts, scenario data, architectural boundaries, and placeholders only. It does not contain a working server or scenario engine.

## Safety boundary

All scenario content and validation rules are illustrative software test fixtures. They do not establish correct clinical care, firefighting tactics, certification readiness, or operational authority.
