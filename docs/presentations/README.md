# Project presentation package

This folder contains the meeting/presentation package for the emergency training simulator POC.

Use it when you need to explain the project to a class, campus job reviewer, advisor, lab group, or early stakeholder.

This is the talk-through deck. For the denser submit-ready report, see `docs/reports/`.

## Files

- `project-overview-slides.md`: editable slide deck source
- `project-overview-speaker-notes.md`: slide-by-slide notes
- `project-overview-read-through-script.md`: a spoken script in a natural, chill tone
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
