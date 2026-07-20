# Local Presentation Webpage

This React, TypeScript, Vite, and Tailwind interface presents the existing deterministic backend demo in a cleaner one-page format.

It does not own scenario state. The browser fetches four guided paths from FastAPI, sends their actions through the existing WebSocket contract, and then displays the backend-generated session review.

The guided expected and review paths are intentionally scripted so a presentation can be repeated reliably. A separate **seeded exploration** developer tool asks the backend to generate a varied simulated-trainee action sequence. Its visible seed makes the exact sequence reproducible. This mode is deterministic pseudo-random exploration—not AI generation and not real trainee behavior.

Every completed path ends with a backend-generated instructor review message. It collects recorded evidence and suggests a discussion prompt, while clearly stating that it is not a grade, validated rubric, or operational judgment.

The **user-controlled** path opens an action-selection screen instead of running a script. Each button sends one action through the normal WebSocket contract and shows the backend response immediately. Finishing the run produces the same instructor finale and full review used by the other paths.

## Run locally

For the recommended one-port presentation workflow, run from the repository root:

```powershell
python scripts/run_web_demo.py
```

Open `http://127.0.0.1:8765`. FastAPI serves the built page and owns all scenario state.

For frontend development, start FastAPI on port `8765`:

```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8765
```

In a second terminal:

```powershell
cd web
npm install
npm run dev
```

Vite serves the webpage on port `5173` and locally proxies `/api`, `/health`, and `/ws` to FastAPI on port `8765`. This two-port mode is recommended only while developing the frontend.

Use `npm run build` for a production build and `npm run lint` for frontend linting.

This remains a deterministic proof of concept. Its results are not clinical validation, operational guidance, protocol authority, or real trainee scoring.

## Funding-proof direction

The current console remains the deterministic session and review baseline. A mocked instructor workflow now lets a user request a scenario suggestion, see visible local job stages, edit all scenario content, and approve or reject a specific revision.

This uses fake local job progress and fixture data. No real model call is hidden behind the interface. The AI role is suggestion only; the instructor owns the title, goals, environment, duration, cues, actions, transitions, end conditions, assets, constraints, notes, and approval decision. After the workflow is reviewed, CS Launch can host the long-running application while VT ARC handles approved generation jobs. Unreal remains the eventual trainee runtime and physics environment.

See `docs/architecture/funding-proof-platform.md` for the full platform split and safety boundaries.
