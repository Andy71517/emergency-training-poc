# Session Logging and Review

The logger writes one JSON object per line so a session can be replayed later.

Each record keeps the input message, validation result, state snapshot, IDs, and sequence number. The review helper turns those records into a short post-scenario summary.

For repository-wide implementation and evidence, see [current status](../../../docs/current-status.md)
and the [documentation index](../../../docs/README.md).
