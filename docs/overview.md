# POC Overview

This POC answers one practical question:

Can a simple trainee action move through the backend and come out as checked, logged, client-ready scenario state?

The current answer is yes, in a small local slice. The backend accepts manual or scripted actions, loads the scenario, applies one deterministic transition, checks the action against POC rules, writes a JSONL log entry, and sends the updated state back over WebSocket.

“Deterministic” just means the same ordered inputs should always produce the same output. That makes the system easier to test, replay, and debug.

## Safety boundary

The scenario and rules are software fixtures. They are useful for proving the code path, not for teaching real medical care, firefighting tactics, certification readiness, or field decisions.
