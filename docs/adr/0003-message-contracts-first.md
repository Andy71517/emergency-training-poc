# ADR 0003: Define Message Contracts First

## Status

Accepted for POC.

## Context

Backend, scripts, future Unreal, and future adapters need a shared vocabulary before their implementations diverge.

## Decision

Version JSON Schemas and examples for actions, state, validation, and session envelopes before endpoint implementation.

## Consequences

Clients can develop against fixtures and boundary tests can fail early. Schema evolution will require explicit compatibility decisions.
