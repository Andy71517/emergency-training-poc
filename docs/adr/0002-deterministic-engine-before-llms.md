# ADR 0002: Build the Deterministic Engine Before LLM Integration

## Status

Accepted for the POC.

## Current implementation note - October 28, 2026

This decision governs deterministic trainee-session transitions. The separate
spatial studio now calls a hosted ARC planner and has an implemented generation
lane; those outputs do not become session truth or validated training decisions.
See [current status](../current-status.md). The original first-slice rationale
below is retained.

## Context

LLMs can be useful later, but they add uncertainty. If state changes are generated unpredictably, bugs become harder to explain and replay.

## Decision

For the first slice, scenario state changes come only from versioned scenario data and deterministic code. There are no real LLM or external AI calls.

## Consequences

Runs are easier to test, replay, and debug. If AI-assisted authoring or adaptation is added later, it should produce bounded suggestions that still go through review and contracts.
