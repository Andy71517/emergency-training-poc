# ADR 0002: Build the Deterministic Engine Before LLM Integration

## Status

Accepted for POC.

## Context

Non-deterministic generation would make transition defects, replay differences, and validation behavior difficult to isolate.

## Decision

Scenario state changes come only from versioned scenario data and deterministic code. No real LLM or external AI call is part of the first slice.

## Consequences

Runs are reproducible and testable. AI-assisted authoring or adaptation must later produce bounded proposals behind explicit review and contracts.
