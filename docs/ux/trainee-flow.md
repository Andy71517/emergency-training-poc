# Trainee flow

This describes the future trainee experience.

The session baseline supports manual, scripted and user-clicked web actions. The separate spatial studio has Blender/Unreal rooms and physics demonstrations. A connected immersive trainee client, sensor input and full gameplay are still future work. See [current status](../current-status.md).

## Current POC flow

```text
scripted trainee action
  -> backend receives action
  -> scenario state updates
  -> validation result is created
  -> client receives state update
  -> log is written
```

## Future trainee experience

Later, the trainee should be able to:

1. start a training session
2. observe a simple scenario
3. notice environmental cues
4. choose or perform actions
5. see the scenario respond
6. finish the scenario
7. receive a review through the instructor/reviewer side

## What the trainee should understand

The trainee should understand:

- what scenario they are in
- what phase the scenario is currently in
- what environmental cues are visible
- whether their action changed the state
- whether the system is warning them about a missed cue

## What the trainee should not control

The trainee/client should not directly control:

- scenario state
- validation status
- final outcome
- review summary
- replay result

The trainee can attempt actions. The backend decides what happened.

## Current example

In the smoke-room POC:

- the wooden chair can block the path
- the entry door starts closed
- the trainee should move the chair and open the door before entering
- ignoring these cues produces warnings or errors

This is not real emergency guidance. It is a software fixture for testing the loop.

