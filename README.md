# Emergency Training Simulator POC

This repo is a small proof of concept for a much larger emergency-response training simulator vision.

The long-term project goal is an AI-driven, adaptive emergency-response training platform with immersive environments, trainee sensing, validation, and scalable deployment.

The goal of this repo is not to build that final product yet. The goal is to prove one simple foundation loop: a trainee does something, the backend receives it, the scenario state changes in a predictable way, the result gets checked, the client receives the new state, and the session is logged for review.

This is not a real training system, medical tool, firefighting authority, or incident-response system.

## The loop we are proving

```text
manual/stubbed trainee action
  -> backend receives event
  -> scenario engine updates state
  -> validation rules check the transition
  -> final scenario state is produced
  -> client-facing state message is available
  -> event and outcome are logged for review
```

Right now this uses one tiny scenario, a FastAPI WebSocket, deterministic Python code, and local JSONL logs. Future AI pieces might help create or adapt scenarios later, but this first version does not need real AI calls.

For the full north-star project vision, see [docs/full-project-vision.md](docs/full-project-vision.md). For the split between current POC work and future full-system work, see [docs/roadmap.md](docs/roadmap.md). For a direct comparison between the original full-system goals and the current repo, see [docs/full-system-gap-map.md](docs/full-system-gap-map.md).

Dr. Cameron's latest funding feedback makes AI-generated scenario drafts and AI-generated, physics-ready asset research the next proof priorities. The deterministic demo remains the trusted baseline. The approved platform direction uses CS Launch for the future web application, VT ARC for heavy generation jobs, and a local or training-room workstation for Unreal and physics. See [docs/architecture/funding-proof-platform.md](docs/architecture/funding-proof-platform.md).

## Setup and run

Use Python 3.11 or newer.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m uvicorn backend.app.main:app --reload
```

For the cleanest end-to-end walkthrough, run the one-command local demo:

```powershell
python scripts/run_local_demo.py
```

It starts the backend if needed, runs demo sessions, replays the logs, prints review summaries, and shows the wooden-chair environment preview with physics disabled and enabled.

For a guided, presentation-friendly backend walkthrough with menu choices, run:

```powershell
python scripts/run_menu_demo.py
```

This default presentation mode announces a brief 2.5-second pause before each run, keeps the first review concise, and offers to show the full action sequence. When running all four paths, it asks before moving to the next one so the audience can catch up or exit early.

For developer checks with no intentional delay or between-run prompts, run:

```powershell
python scripts/run_menu_demo.py --fast
```

Both modes use the same deterministic backend behavior and JSONL logs. The menu can run happy and warning paths for both toy scenarios, replay or summarize saved logs, compare two reviews, show backend status, list scenarios, and accept a small custom action sequence.

## Local presentation webpage

The one-page React demo turns the four guided backend-owned paths and review summaries into a meeting-friendly visual console. It adds presentation pacing, a live action trail, plain-English state changes, and an expandable action-by-action review without changing scenario ownership or validation rules.

The webpage now also includes the first mocked **Scenario and Asset Studio** workflow. An instructor can request a local fixture suggestion, edit every scenario-content field, save a new revision, reject the suggestion, or explicitly approve the exact revision they reviewed. The mock is deliberately labeled: it makes no AI, API, CS Launch, or ARC call. It tests the authority and review experience before real model integration.

The four guided paths remain scripted so the live presentation is predictable. The webpage also has a separate **seeded exploration** mode: the backend creates a varied sequence of simulated-trainee inputs and displays the seed needed to reproduce it. This is deterministic pseudo-random exploration, not AI generation or real trainee behavior.

A **user-controlled smoke-room path** lets a person choose one action at a time. Every choice goes through the same backend session, deterministic rules, state updates, JSONL logging, and final instructor review as the guided paths. It demonstrates the shape of a future trainee interaction, but it is not protocol instruction, validated assessment, or trainee scoring.

For the recommended meeting setup, run one local command:

```powershell
python scripts/run_web_demo.py
```

Then open `http://127.0.0.1:8765`. This builds the React page and serves it from FastAPI on one local port, reducing moving parts during a presentation.

While actively editing the frontend, use the classic two-terminal development workflow. Start FastAPI on port `8765`:

```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8765
```

Then start Vite on port `5173`:

```powershell
cd web
npm install
npm run dev
```

Open the local URL printed by Vite. This development mode keeps each service independently restartable and provides live frontend updates. Both workflows are entirely local and use the same FastAPI-owned state, WebSocket contract, and review endpoints.

The repo now has two deterministic toy scenarios: a smoke-room scenario and a blocked-exit hallway scenario. They track simple environment cues like scans, doors, obstacles, communication, visibility, environment monitoring, exit path status, and occupant handling. The smoke-room path also frames explicit access and observation progress states, so actions remain blocked until the toy scene makes them available. If the trainee skips a cue or attempts an unavailable action, the backend returns a POC warning or error and the review explains what happened in plain English.

In another terminal, run the fake trainee demo:

```powershell
python scripts/run_fake_trainee.py
```

To test the future Unreal client contract, without building an Unreal scene:

```powershell
python scripts/run_unreal_contract_harness.py
```

Run tests, create a fresh session log, and inspect it:

```powershell
python -m pytest -q
python -m ruff check backend scripts
python -m compileall -q backend scripts docs\presentations\build_pdf.py docs\reports\build_report_pdf.py
python scripts\check_json_files.py
python scripts/run_menu_demo.py --fast
python scripts/replay_session.py logs/sessions/YOUR_CURRENT_SESSION.jsonl
python scripts/summarize_log.py logs/sessions/YOUR_CURRENT_SESSION.jsonl
```

Clients start by sending `{"message_type":"start_session"}` to `/ws/sessions/{session_id}`. After that, they send ordered `trainee_action` messages. Generated session logs live under `logs/sessions/` and are ignored by Git.

## Documentation PDFs

Markdown files are the editable source. The submission packet PDFs are the clean shareable copies for Dr. Cameron, reviewers, clients, or future teammates.

The official packet should stay small. Right now it contains four PDFs:

- project overview report
- one-page handout
- roadmap
- full project vision

When an important packet-facing Markdown doc changes, rebuild the packet:

```powershell
python scripts/build_doc_pdfs.py
```

The meeting deck and submit-ready report also have their own polished PDF builders:

```powershell
python docs/presentations/build_pdf.py
python docs/reports/build_report_pdf.py
```

## What this repo is not doing

These statements describe the working code today. The new funding-proof track will explore a few of them as isolated, measured experiments; they are not implemented merely because they now appear on the roadmap.

- Real LLM or external API calls
- Clinical validation or EMT/firefighter protocol authority
- Production security, scaling, deployment, or cloud infrastructure
- Hub-and-spoke networking
- Projection mapping
- Multimodal sensing
- A full Unreal scene
- Generated 3D assets
- Real physics simulation
- Autonomous evaluation of real responders

## Security baseline

The backend now has a small POC security baseline. It rejects strange IDs, unexpected message fields, path-like scenario names, oversized/nested payloads, too many active sessions, and too many actions in one session.

This does not make the app production-secure. There is still no authentication, authorization, TLS, rate limiting, cloud deployment, or real data handling policy.

Start with [docs/security/README.md](docs/security/README.md) for the current trust boundary.

## Repository map

- `backend/`: FastAPI backend, deterministic engine, validation, logging, and tests
- `schemas/`: JSON message contracts and examples
- `scenarios/`: small scenario definitions
- `validation/`: rule files for the toy scenario
- `docs/`: scope, architecture notes, ADRs, and demo flow
- `docs/development/`: local development and lightweight CI notes
- `docs/reference/`: source/reference docs for the larger project vision
- `docs/reports/`: denser submit-ready written reports and report PDFs
- `docs/submission-packet/`: official small generated PDF packet for sharing or submission
- `docs/security/`: POC threat model, client trust boundary, and security roadmap
- `docs/ux/`: trainee, reviewer, and demo experience notes
- `scripts/`: local demo, replay, summary, and contract helpers
- `logs/`: local JSONL session logs, ignored by Git
- `unreal/`: future Unreal client contract and placeholder folder
- `assets/`: placeholder folders and review docs for a future generated/reviewed asset pipeline

Start with [docs/full-project-vision.md](docs/full-project-vision.md), [docs/overview.md](docs/overview.md), [docs/roadmap.md](docs/roadmap.md), and [docs/full-system-gap-map.md](docs/full-system-gap-map.md).
