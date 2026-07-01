# Scenarios

Scenario YAML files define the toy worlds used by the POC.

Each scenario should be small and readable. It should include the starting state, allowed actions, transition rules, validation hints, end conditions, and the expected happy path.

The current smoke-room scenario includes a wooden chair as environment state. It can block the entry path until the deterministic `move_obstacle` action clears it.

These scenarios are software fixtures, not medical guidance, clinical validation, firefighter/EMT protocol, or certification material.

Keep them versioned, reviewable, deterministic, and free of hidden executable logic.
