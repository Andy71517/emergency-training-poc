# Reports and submission packet

The report source and PDF now describe the current studio, asset workflow, evidence
levels and remaining checks as of October 28, 2026. [Current status](../current-status.md)
is the operational evidence index; older handoffs remain dated history.

- [Report source](project-overview-report.md)
- [Standalone report PDF](emergency-training-poc-report.pdf)
- [Presentation package](../presentations/README.md)

From the repo root:

```powershell
python docs/reports/build_report_pdf.py
python docs/presentations/build_pdf.py
python scripts/build_doc_pdfs.py
```

The last command rebuilds the four-file packet in `docs/submission-packet/`:
project report, one-page handout, roadmap and full vision. It replaces that generated
packet's PDFs. Markdown is the editable source; inspect the exported pages after
changes. Folder READMEs stay on GitHub and do not need PDF copies.

The report/deck are communication artifacts, not independent runtime evidence.
They must preserve the distinction between tested code, fixture preparation,
user-confirmed baseline and outstanding live GPU/engine checks.
