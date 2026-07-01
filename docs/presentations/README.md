# Project presentation package

This folder contains a beginner-friendly presentation package for the emergency training simulator POC.

Use it when you need to explain the project to a class, campus job reviewer, advisor, lab group, or early stakeholder.

## Files

- `project-overview-slides.md`: editable slide deck source
- `project-overview-speaker-notes.md`: slide-by-slide notes
- `project-overview-read-through-script.md`: a spoken script in a natural, chill tone
- `project-overview-one-page-handout.md`: short handout version
- `presentation-timing-and-design.md`: suggested 5-minute talk, 5-minute demo flow, and slide design direction
- `emergency-training-poc-overview.pdf`: generated PDF deck
- `build_pdf.py`: small no-dependency PDF builder for this deck

## Rebuild the PDF

From the repo root:

```powershell
python docs/presentations/build_pdf.py
```

The PDF is intentionally simple. It is meant to be readable, easy to share, and easy to regenerate without installing presentation software.
