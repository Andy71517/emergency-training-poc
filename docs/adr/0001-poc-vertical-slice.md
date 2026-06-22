# ADR 0001: Prove a Local Vertical Slice

## Status

Accepted for POC.

## Context

The concept spans AI, simulation, sensing, rendering, networking, and deployment. Building across all of them would hide the core integration risk.

## Decision

First prove one local loop from stub action through deterministic transition, validation, client-facing state, and append-only log.

## Consequences

The POC yields an end-to-end seam early. Production concerns and richer interfaces remain intentionally unanswered.
