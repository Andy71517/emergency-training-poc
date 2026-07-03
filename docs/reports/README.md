# Reports

This folder contains denser written reports for submission or longer review.

This is separate from `docs/presentations/`.

Use:

- `docs/presentations/` for meeting slides and speaker notes
- `docs/reports/` for submit-ready written material

## Files

- `project-overview-report.md`: editable report source
- `emergency-training-poc-report.pdf`: generated report PDF
- `build_report_pdf.py`: small no-dependency report PDF builder

The report PDF is denser than the meeting deck. It is meant to be submitted or read directly, while the presentation PDF is meant to be talked through in a meeting.

## Rebuild the report PDF

From the repo root:

```powershell
python docs/reports/build_report_pdf.py
```
