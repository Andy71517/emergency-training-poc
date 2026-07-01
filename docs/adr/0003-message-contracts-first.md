# ADR 0003: Define Message Contracts First

## Status

Accepted for the POC.

## Context

The backend, scripts, future Unreal client, and future adapters all need to agree on the shape of messages. Without that, each part can drift in a different direction.

## Decision

Keep JSON Schemas and examples for actions, state, validation results, and session messages.

## Consequences

Clients can build against fixtures, and tests can catch contract breaks early. If the schema changes later, compatibility has to be a deliberate choice.
