# Presentation timing and design

This deck is for a live meeting. It is not the submit-ready report and it is not the submission packet.

Use the files this way:

- `docs/submission-packet/`: send or submit
- `project-overview-slides.md`: talk through live
- `project-overview-speaker-notes.md`: presenter context
- `project-overview-read-through-script.md`: practice script
- `python scripts/run_local_demo.py`: proof on screen

## Target timing

Aim for:

- 5 minutes of slides
- 5 minutes of demo

That gives enough time to explain the idea without turning the meeting into a lecture.

## Live slide flow

Use the full deck, but move quickly.

1. Title
2. Short version
3. Why this project exists
4. Trap I am avoiding
5. Core loop
6. What works now
7. Current demo scenario
8. Chair and door
9. Review as proof point
10. Trust boundary
11. Security baseline
12. Future Unreal role
13. Packet vs deck
14. Next steps
15. Demo plan
16. Closing

If time is tight, skip slides 11, 12, and 13 live. Keep them ready for questions.

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
6. chair and door cue status

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
