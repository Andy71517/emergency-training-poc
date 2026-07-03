# Review summary format

The review summary is one of the strongest proof points in the POC.

The goal is not just:

> The demo ran.

The better goal is:

> The system can explain what happened.

That matters for Dr. Cameron because the project is easier to evaluate when the output shows the reasoning trail clearly.

## What the review should answer

A good review should answer:

- What session ran?
- What scenario ran?
- What actions happened, in what order?
- What did validation return?
- What was the final phase?
- Did the scenario end?
- Did replay verify the log?
- Were environmental cues handled?
- What warnings or errors should be discussed?

## Current review sections

The human-readable review is organized as:

1. Session basics
2. Plain-English "what happened" headline
3. Review snapshot
4. Replay verification
5. Action timeline
6. Environment cues
7. Warnings
8. Errors
9. Key observations
10. Reviewer takeaways

## Why this format works

The format separates facts from interpretation.

Facts:

- action order
- validation status
- final phase
- environment object state
- replay result
- whether cue checks like chair, door, and smoke/visibility were handled

Interpretation:

- key observations
- reviewer takeaways

This keeps the review useful without pretending to be clinical scoring, firefighter protocol authority, or EMT guidance.

## Example takeaway

Good:

> The trainee attempted to enter while the entry door was still closed, so the POC validation layer returned a warning and the scenario did not advance.

Also good:

> The trainee cleared the chair and opened the door, but attempted entry before checking the smoke/visibility cue. The POC validation layer returned a warning and kept the scenario from advancing.

Avoid:

> The trainee failed the emergency response.

The first sentence explains the software behavior. The second sentence overclaims.

## Current command

Run:

```powershell
python scripts\summarize_log.py logs\sessions\<session-id>.jsonl
```

For raw structured JSON:

```powershell
python scripts\summarize_log.py logs\sessions\<session-id>.jsonl --json
```
