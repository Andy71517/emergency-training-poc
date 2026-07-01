# ADR 0002: Build the Deterministic Engine Before LLM Integration

## Status

Accepted for the POC.

## Context

LLMs can be useful later, but they add uncertainty. If state changes are generated unpredictably, bugs become harder to explain and replay.

## Decision

For the first slice, scenario state changes come only from versioned scenario data and deterministic code. There are no real LLM or external AI calls.

## Consequences

Runs are easier to test, replay, and debug. If AI-assisted authoring or adaptation is added later, it should produce bounded suggestions that still go through review and contracts.
