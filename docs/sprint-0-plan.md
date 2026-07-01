# Sprint 0 Plan

## Goal

Keep the first build honest and small.

Before adding anything fancy, the repo should prove the basic path from action to state to log. The docs and contracts also need to make it obvious what belongs in the backend, what belongs in a future client, and what is not part of this POC.

## Work items

1. Set clear repo boundaries and non-goals.
2. Define the main message shapes: trainee action, scenario state, validation result, and session messages.
3. Add one tiny smoke-room scenario and matching rule file.
4. Record decisions about determinism, ownership, message contracts, and validation limits.
5. Build the first local backend slice.
6. Add helper scripts for demo, replay, summary, and the future Unreal client contract.
7. Keep Unreal and asset work as placeholders until there is a real reason to build them.

## Exit criteria

- The repo is easy to navigate.
- The local backend loop works.
- Current work and future ideas are clearly separated.
- The project does not depend on AI services, sensors, rendering, or distributed networking.
