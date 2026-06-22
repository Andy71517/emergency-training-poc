# ADR 0004: Unreal Is Not the Source of Truth

## Status

Accepted for POC architecture.

## Context

Embedding authoritative scenario logic in a presentation client would make replay, alternate clients, and consistent validation harder.

## Decision

The backend owns session order, transitions, validation results, and logs. Unreal eventually submits normalized actions and renders returned state.

## Consequences

The engine remains client-neutral and testable without Unreal. The client must tolerate authoritative state correction and network delay in future deployments.
