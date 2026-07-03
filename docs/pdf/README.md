# Generated Documentation PDFs

This folder holds PDF copies of audience/client/future-teammate-facing Markdown docs.

The Markdown files are still the source files. These PDFs are the easier-to-share versions for reading, submitting, or sending to someone like Dr. Cameron.

## Rebuild PDFs

From the repo root:

```powershell
python scripts/build_doc_pdfs.py
```

You can also rebuild only one or two files:

```powershell
python scripts/build_doc_pdfs.py README.md docs/roadmap.md
```

When an important Markdown file changes, rebuild the matching PDF too.

Folder READMEs do not need PDFs. GitHub already displays those nicely.

The presentation deck and report still have their own nicer builders:

```powershell
python docs/presentations/build_pdf.py
python docs/reports/build_report_pdf.py
```
