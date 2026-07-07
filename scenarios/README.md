# Scenarios

Scenario YAML files define the toy worlds used by the POC.

Each scenario should be small and readable. It should include the starting state, allowed actions, transition rules, validation hints, end conditions, and the expected happy path.

Current scenarios:

- `smoke_inhalation_room_v0`: a smoke-room POC with a wooden chair, an entry door, communication, visibility, monitoring, and occupant-search cues.
- `blocked_exit_hallway_v0`: a hallway POC with a collapsed bookshelf, a secondary exit door, visibility, communication, environment monitoring, and occupant-guidance cues.

For now, these are deterministic software cues only. Door lock state, door type, hinge side, swing direction, collision shape, mass, force directions, smoke behavior, visibility behavior, and obstacle physics are metadata.

These scenarios are software fixtures, not medical guidance, clinical validation, firefighter/EMT protocol, or certification material.

Keep them versioned, reviewable, deterministic, and free of hidden executable logic.
