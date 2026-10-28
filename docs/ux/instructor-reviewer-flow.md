# Instructor/reviewer flow

The current session review presents actions, findings and replay evidence. The spatial studio also exposes saved plans, jobs, assets, worker reports and recordings. Domain-reviewed instruction, annotations and approved training publication remain future work. [Current status](../current-status.md).

For the first POC, the reviewer is the most important user.

The reason is simple: if the system cannot explain what happened afterward, it is not very useful for training.

## Current POC flow

After a session, the reviewer can inspect:

- actions taken
- final state
- warnings
- errors
- environment cue status
- whether the end condition was reached
- whether replay verification passed

## What the reviewer should learn

The reviewer should be able to answer:

- What did the trainee attempt?
- What order did the actions happen in?
- Did the scenario state change?
- Were any environmental cues ignored?
- Did validation return warnings or errors?
- Did the scenario reach an end condition?
- Can the session be replayed consistently?

## Current review format

The current review output is organized around:

- session basics
- action timeline
- final state
- environment cues
- warnings
- errors
- key observations
- reviewer takeaways

See `review-summary-format.md` for the current format.

## What the review should avoid

The review should avoid pretending to be:

- clinical evaluation
- certification scoring
- official firefighting guidance
- official EMT guidance
- real-world performance judgment

The review is a POC explanation of a deterministic scenario run.

## Good review wording

Good:

> The trainee attempted to enter while the entry door was still closed, so the POC validation layer returned a warning and the scenario did not advance.

Avoid:

> The trainee failed the correct emergency protocol.

The first sentence explains software behavior. The second overclaims.
