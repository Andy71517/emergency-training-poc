# Future Hub-and-Spoke Topology

**Status: future exploration; excluded from the POC.**

A later deployment may place an authoritative session service at a hub and connect presentation, instructor, sensor, and logging clients as spokes. Before that decision, the local vertical slice must prove stable contracts, ordering, idempotency expectations, reconnect behavior, and state snapshots.

Sprint 0 does not select a broker, protocol, discovery mechanism, or distributed consistency model. No hub-and-spoke networking should be added to the first implementation.
