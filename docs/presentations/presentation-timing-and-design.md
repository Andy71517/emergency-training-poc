# Presentation timing and design

This deck is for a live meeting. It is not the submit-ready report and it is not the submission packet.

Use the files this way:

- `docs/submission-packet/`: send or submit
- `project-overview-slides.md`: talk through live
- `project-overview-speaker-notes.md`: presenter context
- `project-overview-read-through-script.md`: practice script
- `dr-cameron-demo-runbook.md`: screen-share checklist and live demo flow
- `python scripts/run_local_demo.py`: proof on screen

## Target timing

Aim for:

- about 7 minutes of slides if the audience needs the full origin story
- 5 minutes of demo
- 5 minutes for questions and feedback

If time is tight, compress the slides to 5 minutes by moving quickly through the timeline and boundaries.

## Live slide flow

Use the full deck, but move quickly.

1. Title
2. Original full-system vision
3. First useful question
4. Solo-dev checkpoint strategy
5. Sprint 0 scaffold
6. First working backend loop
7. Review as proof point
8. Environmental cues
9. Second scenario
10. Unreal as display client
11. Current architecture
12. Timeline
13. Boundaries
14. Demo and feedback
15. Closing

If time is tight, move quickly through slides 5, 9, and 12. Keep the detail in speaker notes.

## Demo flow

Run:

```powershell
python scripts/run_local_demo.py
```

Show:

1. backend starts or is detected
2. happy path session
3. warning/error session
4. replay verification
5. review summary
6. environmental cue status

If Unreal is ready, also show the text debug panel after the backend demo.

Frame Unreal carefully:

> This is the first display-client step. The backend still owns scenario truth.

Main demo sentence:

> The important part is not only that the demo ran. It is that the system can explain what happened afterward.

## Design direction

Use the deck like a conversation aid.

Good slide rules:

- one main idea per slide
- short bullets only
- no dense paragraphs
- no tiny code blocks
- leave breathing room
- explain details out loud, not on the slide

## Visual style

Use:

- azure blue for backend/trust/system structure
- amber for attention, warnings, and emergency-training energy
- off-white or very light blue backgrounds
- simple dividers and accent bars

Avoid:

- dramatic emergency stock imagery
- fake clinical authority
- cyberpunk dashboards
- slides that look like reports pasted into PDF form

## Presenter style

Keep the voice grounded:

- "Here is what I built."
- "Here is what it proves."
- "Here is what it does not prove yet."
- "Here is why I built it in this order."
- "Here is the next careful step."

That should land well with Dr. Cameron because it shows progress and judgment, not just ambition.

## Solo developer framing

Say this out loud early:

> This is a large project for one person, so I am treating the full vision as the north star and the POC as a sequence of checkpoints.

That framing helps the audience judge the work fairly. It also explains why the project delays Unreal scenes, generated assets, real physics, sensing, and AI calls until the foundation has a clear job for them.

## Audience tone

The first audience is Dr. Melissa Cameron, who is also the project supervisor for the on-campus job.

The tone should be:

- clear enough for a mixed audience
- respectful and prepared
- honest about limits
- casual enough to sound like me
- focused on judgment, not hype

## Is the packet enough?

The packet is enough as a reading bundle or leave-behind.

It is not enough as the live presentation by itself.

Use the packet when someone wants to read the project later. Use the deck and runbook when presenting on screen.
