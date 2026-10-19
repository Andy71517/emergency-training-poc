# Fieldwork scenario workspace — local single-user POC

This batch adds the frontend for real ARC prompt planning and persistent layout review. Blender/Unreal workers are visibly not connected; their previously verified desktop workflows remain separate. No live Unreal stream or automatic repair button is claimed.

## Windows setup (first time)

On your PC, open PowerShell in a folder where you want a fresh project copy. Git, Python3.11+ and a Node version supported by the checked-in Vite package must be installed. The repository is private: Git may open a GitHub login prompt. No ARC login-node checkout is used for this web application.

```powershell
git clone --branch codex/arc-scenario-workspace https://github.com/Andy71517/emergency-training-poc.git emergency-training-studio
cd emergency-training-studio
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
npm --prefix web ci
npm --prefix web run build
Copy-Item backend\.env.example backend\.env
notepad backend\.env
```

In Notepad set ARC_LLM_API_KEY to your personal key, retain ARC_LLM_MODEL=gpt-oss-120b, save and close. backend/.env is ignored by Git. Never put the key into the frontend, prompt, browser storage, VITE variables, chat or screenshot. Config reads only those two keys from this simple dotenv file; environment variables take precedence. Do not use export prefixes or multiline values. Existing configured files should not be overwritten when updating an existing checkout.

Start from the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8765
```

Keep PowerShell running, then open http://127.0.0.1:8765 in your browser. The backend serves the built frontend and API together; a second terminal/Vite server is unnecessary. Run one backend process only. Do not use --reload or multiple workers during an active generation job. If port8765 is occupied, stop the earlier local POC process first.

## First real frontend request

1. Verify ARC configured appears. It means a key is present, not that a live call has already succeeded.
2. Enter a scenario brief, layout count1-30 and seed. The backend sends the real prompt to ARC's hosted gpt-oss-120b service. Nothing runs on your laptop GPU.
3. Click Generate batch. Queued -> Interpreting prompt -> Building layouts -> Ready for review. Status polling runs every2.5s. Up to four active jobs, one model request at a time.
4. Review all returned layouts and plan assumptions. Click a layout to enlarge it and download its scene JSON. Escape closes it. Plan/manifest downloads are below the gallery. Saved jobs remain in the sidebar after refresh/restart.
5. Return one whole-workspace screenshot and any error. This is the first actual browser-to-ARC integration run; local visual tests used an explicit offline fixture, not your credentials.

Suggested variation prompt to demonstrate genuine adaptation: “Create rectangular classroom-style rooms nine metres wide and seven metres deep, with eight wooden chairs and a1.8-metre central aisle. Use one centred1.2-metre exit. Keep the first two layouts clear and put a chair in the aisle in the last layout.” Use count3. Check the returned dimensions: the earlier first model response simply repeated the provided example. Schema validity is not proof of semantic compliance.

## Scope and behavior

Supports the existing bounded generator: rooms6-10m wide/deep, height2.5-4m, one centred positive-Y doorway, reviewed chair only, seeded clear/obstructed aisle layouts. Unknown assets/smoke/characters/unsupported requests are rejected when identified by the planner; always inspect its interpretation. Over-capacity layout requests fail instead of silently shrinking objects. Aisle overlap is geometric only, not proof of an impassable exit or valid evacuation scenario. First page shows no fake sample generation. Legacy deterministic and browser physics views remain reachable through Legacy POC tools, with a return ARC workspace button.

SQLite jobs and artifacts live under logs/studio (Git ignored). Failed requests retain a sanitized user-facing error; unexpected exceptions use generic errors. Backend restart marks unfinished jobs interrupted; it does not silently spend another model request. Re-submit explicitly. Completed artifacts persist. One-process local development only; this is not a public multi-user service. Loopback binding is required. ARC project/service credentials or increased usage arrangements are a later authorized change.

Blender and Unreal statuses deliberately say Not connected even though separate scripts have already run on Andy's PC. Next integration should attach actual workers and returned scene/video artifacts to this job record, not merely change status labels.

## Verification

Backend suite87passed in an isolated source snapshot. The working scratch directory also contains an ignored wooden-chair-reference.png, which trips an older test asserting no generated files exist; no user asset was deleted to make tests pass. Studio integration tests verify job persistence, artifact boundaries, request bounds, foreign-origin rejection, credential prompt rejection, absence of the test key from persisted jobs/API, and sanitized failure handling. Generator CLI regression tests pass. Frontend production build and ESLint pass. PhysicsLab is lazy-loaded; workspace initial JS about252kB, with the older3.14MB physics chunk loaded only on demand.

Headless Chromium visual tests exercised real HTTP submit/status/gallery/artifact rendering against an explicitly offline planner. Desktop1440px and mobile390px screenshots inspected; mobile sidebar overflow corrected. Live model planning from the UI, Windows installation, and personal-key endpoint connectivity remain to be verified by Andy. No new ARC/Blender/Unreal work is automatically launched by this frontend batch.
