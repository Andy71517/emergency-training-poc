# Trainee session client contract

This folder specifies a thin WebSocket session client: start a session, send
ordered trainee actions, receive state/findings/end messages and display them.
The harness exercises that contract without a rendered Unreal scene.

This is separate from the implemented local editor bridge used for map assembly,
Chaos batches and recordings. The full trainee WebSocket/immersive gameplay client
is still future integration work. [Unreal integration](../README.md).

- [Session messages](client-contract.md)
- [Client state machine](client-state-machine.md)
- [Display contract](state-display-contract.md)
- [Display schema](debug-display-state.schema.json) and [examples](examples/)

The client does not own transitions, validation, scores, logs or review. The backend
owns those records; engine observations and generated appearance are not clinical
or operational truth. [Current status](../../docs/current-status.md).
