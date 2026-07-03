# Lightweight CI

This repo uses a small GitHub Actions workflow as a safety net.

The goal is simple:

Every push should prove the basic POC still works.

## What CI runs

The workflow runs on pushes to `main` and on pull requests.

It checks:

- Python tests
- Ruff linting
- Python compile check
- JSON parse check for checked-in schemas/examples/contracts
- Documentation PDF builder compile check

## Commands

These are the same checks to run locally:

```powershell
python -m pytest -q
python -m ruff check backend scripts
python -m compileall -q backend scripts docs\presentations\build_pdf.py docs\reports\build_report_pdf.py
python scripts\check_json_files.py
```

When audience/client/future-teammate-facing Markdown docs change, also rebuild the PDF copies:

```powershell
python scripts\build_doc_pdfs.py
python docs\presentations\build_pdf.py
python docs\reports\build_report_pdf.py
```

## What CI does not do yet

This is not full DevOps yet.

It does not:

- deploy anything
- build Docker images
- publish releases
- run cloud infrastructure
- run Unreal builds
- generate assets
- run real security scanning
- run the local demo script

Those can come later when the project has something production-like to deploy or package.

## Why this belongs now

CI is useful even in a POC because it catches simple mistakes early.

If tests, lint, compile, and JSON parsing pass, I know the repo is still in a decent state before showing it to someone else.
