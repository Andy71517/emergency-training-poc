# Project presentation package

This folder contains the meeting/presentation package for the emergency training simulator POC.

Use it when you need to explain the project to Dr. Melissa Cameron, a class, campus job reviewer, advisor, lab group, or early stakeholder.

This is the talk-through deck. For the denser submit-ready report, see `docs/reports/`.

## Files

- `project-overview-slides.md`: editable slide deck source
- `project-overview-speaker-notes.md`: slide-by-slide notes
- `project-overview-read-through-script.md`: a spoken script in a natural, chill tone
- `dr-cameron-demo-runbook.md`: live screen-share checklist and demo flow
- `project-overview-one-page-handout.md`: short handout version
- `presentation-timing-and-design.md`: suggested 5-minute talk, 5-minute demo flow, and slide design direction
- `emergency-training-poc-overview.pdf`: generated PDF version of the slide deck
- `build_pdf.py`: small no-dependency PDF builder for this deck

## Rebuild the PDF

From the repo root:

```powershell
python docs/presentations/build_pdf.py
```

This PDF is a deck export. It is meant for meetings and talk-throughs, not as the full submit-ready report.

## Live meeting recommendation

For a Dr. Cameron meeting, use:

1. `emergency-training-poc-overview.pdf` for the talk
2. `dr-cameron-demo-runbook.md` beside the terminal
3. `python scripts/run_local_demo.py` for the backend proof
4. Unreal only if the debug panel is calm enough to show

The packet is still useful as a leave-behind, but the live meeting should focus on the deck, demo, and review summary.

The deck now tells the story from the original full-system idea to the current backend-first POC and the next solo-developer milestones in a shorter meeting-friendly format.
