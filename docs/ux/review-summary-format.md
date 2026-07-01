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
2. Final state and outcome
3. Replay verification
4. Action timeline
5. Environment cues
6. Warnings
7. Errors
8. Key observations
9. Reviewer takeaways

## Why this format works

The format separates facts from interpretation.

Facts:

- action order
- validation status
- final phase
- environment object state
- replay result

Interpretation:

- key observations
- reviewer takeaways

This keeps the review useful without pretending to be clinical scoring, firefighter protocol authority, or EMT guidance.

## Example takeaway

Good:

> The trainee attempted to enter while the entry door was still closed, so the POC validation layer returned a warning and the scenario did not advance.

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

