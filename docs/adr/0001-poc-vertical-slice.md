# ADR 0001: Prove a Local Vertical Slice

## Status

Accepted for the POC.

## Context

The bigger idea touches AI, simulation, sensing, rendering, networking, and deployment. If we try to build all of that at once, we will not know whether the basic action-to-state loop actually works.

## Decision

First, prove one local loop:

```text
stub action -> deterministic state update -> validation -> client message -> log
```

## Consequences

We get a real end-to-end path early. Bigger product questions stay parked until the core loop is solid.
