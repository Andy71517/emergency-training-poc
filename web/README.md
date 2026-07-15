# Local Presentation Webpage

This React, TypeScript, Vite, and Tailwind interface presents the existing deterministic backend demo in a cleaner one-page format.

It does not own scenario state. The browser fetches the four scripted paths from FastAPI, sends their actions through the existing WebSocket contract, and then displays the backend-generated session review.

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
