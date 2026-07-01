# Presentation timing and slide design

This deck is meant to work as a 5-minute project explanation plus a 5-minute demo.

That shape fits the project well because the slides explain the "why," and the demo proves the loop instead of just talking about it.

The first audience is Dr. Cameron, so the presentation should feel like a clear on-campus project update first and a pitch deck second.

## Suggested timing

### 5-minute presentation

Use about 8 to 10 slides live.

Recommended flow:

1. Title and short version
2. Why this project exists
3. The problem I am avoiding
4. The POC loop
5. Where I am now
6. Current scenario
7. Environment cues
8. Validation boundary
9. Security baseline
10. Next goal
11. Closing

The remaining slides are useful backup slides. They are there if someone asks about Unreal, assets, sample results, or long-term direction.

### 5-minute demo

Run:

```powershell
python scripts/run_local_demo.py
```

Demo flow:

1. Show the backend starts or is detected.
2. Show the happy path.
3. Show the warning/error path.
4. Point at the replay verification.
5. Point at the review summary.
6. Point out the chair and door environment cues.
7. Mention that the backend owns the result; the client only requests actions.

The main sentence for the demo:

> This is the proof point: actions go in, state comes out, and the log can explain what happened later.

## Slide design direction

Keep the design simple and clean.

The project is technical, so the slides should feel readable and trustworthy instead of flashy.

Recommended style:

- dark background or soft off-white background
- one main idea per slide
- large titles
- short bullets
- simple diagrams instead of dense paragraphs
- code blocks only when they explain the loop clearly
- no stock emergency imagery unless it is subtle and not dramatic

## Visual theme

A good visual direction would be:

- charcoal / near-black background
- warm orange accent for emergency/training energy
- muted blue accent for backend/system trust
- simple line icons for backend, client, log, replay, and environment objects

This keeps it grounded. Not too corporate, not too cyberpunk, not too "Hollywood firefighter poster."

## Slide layout idea

Use three slide types:

1. Story slides: one sentence plus two or three bullets.
2. System slides: small flow diagram plus short explanation.
3. Demo slides: expected output, warnings, final state, and replay result.

## Design note for later

The current PDF is intentionally plain because it is generated without extra dependencies.

If this becomes a real presentation deliverable, the next step should be a designed version in PowerPoint, Google Slides, Canva, or a Markdown slide tool like Marp.

The content is already structured for that. The visual pass can come after the wording feels right.
