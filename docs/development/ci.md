# Repository checks and CI

The checked-in workflow `.github/workflows/ci.yml` runs on pushes to `main` and pull
requests. Python 3.11 and Node 22 are the CI baselines.

## Exact workflow checks

```powershell
python -m pip install -e ".[dev]"
python -m pytest -q backend/tests arc/tests
python -m ruff check backend scripts
python -m compileall -q backend scripts arc/scripts unreal/scripts docs/presentations/build_pdf.py
python scripts/check_json_files.py
npm.cmd --prefix web ci
npm.cmd --prefix web run lint
npm.cmd --prefix web run build
```

CI also runs `bash -n` on every `arc/scripts/*.sh` and `arc/jobs/*.sbatch`. On
Windows, put Git Bash on PATH for shell-syntax tests; WSL's `bash.exe` cannot use
the same `C:/...` paths. The default `pytest` configuration selects backend tests
only, so name both directories for the complete backend/ARC suite.

The last implementation checkpoint passed 138 backend/ARC tests. Test counts are
dated evidence, not a permanent project requirement. The suite covers persistent
studio/asset jobs, package provenance, SSH recovery/duplicate suppression, MCP
handshake/tool boundaries, worker failures and the deterministic session baseline.

## Documentation exports

After changing packet-facing sources, rebuild:

```powershell
python scripts/build_doc_pdfs.py
python docs/presentations/build_pdf.py
python docs/reports/build_report_pdf.py
```

Review the generated pages for clipping/overflow and verify local Markdown links.
PDF generation/rendering and documentation link checks are manual checks; they are
not currently workflow jobs. `npm audit` and `pip check` are useful additional
dependency checks, but CI does not currently invoke them.

## What CI proves

CI checks source, fixtures, mocked transports/editor behavior and real local MCP
protocol calls. It does not authenticate to ARC, download model weights, run GPU
inference, launch Blender/CoACD preparation, execute Unreal/collision cooking,
capture a live editor recording, deploy services or validate emergency training.
Keep those runtime acceptance results separate in [current status](../current-status.md).
