# Furniture variants: first couch and reusable asset library

## What this batch adds

The frontend now has **Asset library**. A family, such as chair or couch, can contain many named designs. For example:

| Family | Separate variants | Reuse |
| --- | --- | --- |
| Chair | Wooden dining chair, metal folding chair, upholstered armchair | Ten copies of the same design use one model. |
| Couch | Charcoal two-seat couch, leather three-seat couch, sectional | A different design gets a different model. |

The original reviewed wooden chair remains available to the existing room/Chaos demo. New variants follow this workflow:

1. Save a design with a reference PNG, target dimensions and seed.
2. Download its ARC request ZIP.
3. Submit one ARC job; it generates shape and PBR textures with the existing Hunyuan environments.
4. Import the returned `result.zip` into the frontend. Inspect the generated GLB in the 3D viewer.
5. Click **Prepare Blender review copy**. This runs Blender in the background and saves a separate `.blend` file.
6. Inspect orientation, size, geometry and materials in Blender. Prepare and review suitable collision pieces before enabling the new design in room assembly and Chaos.

**This batch implements steps 1–5.** Step 6 needs the actual couch output. The current room schema and Unreal worker still use the original reviewed wooden chair. They do not yet select new library variants from scenario prompts. New designs are clearly marked as unavailable to room assembly; a couch request is never silently fulfilled with a chair.

## 1. Update the local Windows app

Stop the backend with Ctrl+C in its PowerShell window. From the `emergency-training-studio` checkout, on `codex/arc-scenario-workspace`:

```powershell
git pull --ff-only
.\.venv\Scripts\python.exe -m pip install -e .
npm --prefix web ci
npm --prefix web run build
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8765
```

Open `http://127.0.0.1:8765` and refresh the page. Keep the backend running. Blender does not need to be open for background preparation. Unreal is only needed later for room assembly and Chaos; it is not needed for this asset-generation batch.

## 2. Save the first couch design

1. Click **Asset library** in the sidebar. On a narrow screen, use the Asset library link below the scenario prompt.
2. The first design form is filled with **Charcoal two-seat couch** and its prepared reference image.
3. Leave the initial target dimensions at **1.8 m wide × 0.85 m deep × 0.85 m high**, seed **42**.
4. Click **Save design request**. This saves files locally; it does not call ARC or charge the hosted planner.
5. Click **Download ARC request**. Keep the ZIP name unchanged.

The reference image is a generated product image, not a 3D model or an ARC output. Hunyuan is image-to-3D: the PNG guides generation. The description is design metadata, not an additional text-conditioning input. For other designs, upload a clear PNG showing a whole single object, 64–4096 pixels per side, under 8 MB.

## 3. Upload the request to ARC

Connect to VT's VPN and open Open OnDemand as before.

1. Open **Files → Home Directory**.
2. Upload the downloaded `asset-request-….zip` into your home directory. Do not unzip it.
3. Open the Tinkercliffs shell.
4. Update the ARC checkout to this branch. Run each line separately:

```bash
cd "$HOME/emergency-training-poc"
git status --short --branch
git fetch origin
git switch codex/arc-scenario-workspace
git pull --ff-only
```

If `git status` lists changed tracked files, or switching branches fails, stop and share that output. Do not discard files. Your ignored `arc/.env` stays local; do not paste its contents.

5. In the frontend, copy the command shown under **Generate on VT ARC**. Replace `/path/to/` with your home directory, for example:

```bash
bash arc/scripts/submit_hunyuan_variant.sh "$HOME/asset-request-PASTE_THE_ACTUAL_ID_HERE.zip"
```

Use the real filename, not the example placeholder. The frontend displays the exact short ID in the filename. This command reads the existing `arc/.env` account/partition/QoS and uses the previously verified shape and texture runtimes. It does not rebuild either environment or change the original chair outputs.

Expected response: `Submitted batch job NNNNNNN`. This is a GPU job, not a hosted LLM API request; no planner key is required.

## 4. Watch the job

Replace `JOB_ID` with the actual number:

```bash
squeue -j JOB_ID
sacct -j JOB_ID -X --format=JobID,State,ExitCode,Elapsed
tail -n 30 arc/results/hunyuan-variant-JOB_ID.out
```

When it completes, the output prints:

```text
DOWNLOAD THIS FILE: /projects/research-mel/anirudhalledula/emergency-training-poc/hunyuan21/variants/FULL_ASSET_ID/result.zip
```

Use Files in Open OnDemand to browse to that exact folder and download `result.zip`. No need to download the runtime or model checkpoints. If the job fails, share the last 80 lines of its error log, using its actual job number:

```bash
tail -n 80 arc/results/hunyuan-variant-JOB_ID.err
```

Submitting the identical request again reuses a completed result. A file lock prevents two jobs from generating the exact same variant simultaneously. A failed run keeps its intermediate files for diagnosis; a later submission writes a new run folder. The backend cannot monitor ARC's scheduler directly in this handoff route.

## 5. Import and inspect the actual output

1. Return to the local frontend's **Asset library**.
2. Select the couch design card.
3. Click **Import ARC result.zip**, and choose the file downloaded from ARC.
4. The card now says **Generated · Blender review next**. The viewer shows the actual embedded GLB. Drag to orbit; scroll to zoom. Review lighting differs from the reference image.
5. Click **Prepare Blender review copy**. The same `BLENDER_EXECUTABLE` setting already used for rooms is reused. You do not need Blender open.
6. When complete, download **review.blend** and the preparation report. Open the `.blend` in Blender for inspection.

The preparation worker preserves materials, packs embedded textures, centers the geometry in X/Y and places its bottom at Z=0. It scales uniformly to the requested height. It deliberately preserves the generated proportions rather than stretching width and depth to match a target. The report records actual staged dimensions and flags differences over 15%. Orientation and pivots still need inspection. It does not decimate, invent collision pieces, calibrate mass, or claim a physically accurate model.

**Resume point:** share the couch preview/actual staged dimensions and whether its orientation and shape look correct. The next implementation step is collision preparation for this actual mesh, followed by mixed-asset room schemas and variant bindings in Blender/Unreal. The first live couch GPU run and its physics have not been verified here.

## Saved data and design identity

New asset data is stored under `logs/studio/asset-library/`, with records in the existing local SQLite database. These local files are ignored by git. Deleting a scenario batch does not delete reusable assets.

The full asset ID hashes the family, normalized name/description, target dimensions, reference image bytes, shape seed, fixed settings and pinned model/source revisions. Repeating these inputs opens the same design; changing an input creates another design. This compares exact request content, not semantic similarity between differently worded descriptions. The upstream paint process uses its defaults; the system reuses saved results instead of claiming bit-for-bit paint regeneration.

Result imports check the request identity, reference hash, stage completion, declared source/model revisions and file checksums. These checks bind a returned package to a saved request; they are not independent proof of where computation occurred or of mesh quality. ZIP names and expanded sizes are restricted; GLB images/buffers must be embedded. The original request and imported result are retained, along with source notices and patches.

No ARC credential is placed in the request or result ZIP. The hosted planner key remains separate from the GPU workflow. The prepared charcoal couch reference was made with the built-in image-generation tool; its prompt is saved alongside the web reference in `web/public/references/`.

The deployed reference uses WebP encoding for a smaller download. The browser encodes those pixels as PNG before saving a request; the stored PNG bytes determine the reference hash. The full-resolution generated source image is retained in the conversation.
