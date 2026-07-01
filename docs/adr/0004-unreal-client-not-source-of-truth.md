# ADR 0004: Unreal Is Not the Source of Truth

## Status

Accepted for the POC architecture.

## Context

If Unreal owns scenario rules, replay and alternate clients become much harder. The same session could behave differently depending on the client.

## Decision

The backend owns session order, transitions, validation results, and logs. A future Unreal client sends normalized actions and displays the state it gets back.

## Consequences

The engine stays usable by any client and testable without Unreal. A future client must be ready to accept backend state as the final answer, even if there is delay or correction.
