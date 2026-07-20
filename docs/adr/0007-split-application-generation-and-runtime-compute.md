# ADR 0007: Split Application, Generation, and Runtime Compute

## Status

Accepted as the direction for the funding-proof phase.

## Context

The next research phase needs long-running web services, high-memory GPU jobs, and an Unreal runtime. Putting all three jobs on one platform would make deployment harder and would not use the available Virginia Tech resources well.

## Decision

Use three clear execution areas:

- CS Launch for the future web application and job-control services.
- VT ARC for queued AI generation, processing, and benchmarks.
- a local or training-room Windows workstation for Unreal rendering, interaction, and physics.

The existing local setup remains the development and demonstration baseline. Direct CS Launch-to-ARC job submission will not be assumed until the supported institutional integration is confirmed.

Generated scenarios and assets remain drafts until they pass machine checks and human review. The backend remains the source of approved scenario state.

## Consequences

The project can use ARC GPUs without turning the Unreal workstation into a model server. The frontend gains a clear job-monitoring and review role. The separation also creates integration work around identities, job submission, storage, result transfer, retries, and failure reporting.

The first implementation should mock that boundary locally. Real ARC integration comes after access, a measured manual experiment, and confirmation of the approved connection method.
