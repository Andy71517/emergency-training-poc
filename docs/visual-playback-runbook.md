# Visual playback batch — 2026-10-18

## What now works, and what is new

Andy confirmed the existing pipeline on Windows: live ARC generation, Blender assembly, Unreal room assembly, ten-second Chaos runs cycling through every room, and downloadable observations. The ARC certificate issue was resolved by verified Windows native certificate validation.

This batch adds **Record movement demo**. It reuses an assembled batch, applies a fixed input to one chair in each room, captures Unreal frames, encodes MP4 clips and displays those clips with observations in the frontend. It does not make another ARC request or modify saved chair assets/maps during the physics test.

## Update in simple steps

1. Wait for existing work to finish. Stop the backend with Ctrl+C.
2. From the project folder in PowerShell, run:

```powershell
git pull --ff-only
.\.venv\Scripts\python.exe -m pip install -e .
npm --prefix web ci
npm --prefix web run build
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8765
```

3. Keep Unreal open. Stop any active simulation and save your current level.
4. In Unreal, **Tools → Execute Python Script**, then select this checkout's `unreal/scripts/studio_bridge.py` again. This reloads the worker with recording support. It preserves the existing chair mesh binding when reloaded from the prior worker.
5. Refresh http://127.0.0.1:8765. Select a batch whose rooms are already assembled, open **Unreal / Chaos**, and click **Record movement demo**.
6. Keep Unreal visible and let it cycle through the rooms. The target is roughly ten seconds per room, plus frame capture/encoding time. When the frontend says **Ready to watch**, play or download the clips below the controls.

Existing batches can be reused. No `.env` changes or new chair download are needed. The Python install adds imageio-ffmpeg, including a video encoder in supported wheels; no separate FFmpeg application setup is normally required. Normal **Run Chaos batch** remains available without the added chair input or capture.

If the recording button is disabled, check Connections: the updated editor worker and video encoder both need to be ready. If frames were captured but encoding failed, **Retry encoding saved frames** retries only the local encode. If screenshot capture itself failed, record a new demo and share the displayed error. Do not share your ARC key.

## What the test measures

- Choose the front-most dynamic chair, breaking ties by its instance label.
- About two seconds after simulation starts, call `add_velocity_change_impulse_at_location` once with input `(0, 180, 0)` in engine velocity-change units and an application point 65 cm above the chair component origin. This is a fixed demonstration input, not a measured physical push or calibrated force.
- Sample target position and speed during editor ticks. A displacement of at least 5 cm satisfies the visible-movement check. A linear speed below 8 cm/s and angular speed below 8 degrees/s for the final continuous second is reported as settled at the end.
- Preserve all-chair initial/final positions and the controlled input in each recording's own observations file. A later normal run does not replace a clip's associated evidence.
- The floor-origin Z value is recorded as a raw observation, not a floor-penetration/collision test. Contacts, evacuation behavior and real-world physics validity remain unverified.

## How recording works

The worker uses Epic's `AutomationLibrary.take_high_res_screenshot` with the room review camera, a 960×540 output and game view enabled. It requests up to five frames per second, waiting for each asynchronous screenshot task before requesting another. Frame completion timestamps are recorded; a frame save timeout is reported rather than hidden. The backend creates H.264 MP4 with timestamp-based holds between captured images and 24 fps output for browser compatibility. This does **not** mean Unreal was captured at 24 fps. Measured capture rate is shown beside every clip; timing is approximate wall-clock timing and capture can affect engine performance. This is saved playback, not live streaming or a deterministic physics benchmark.

Clips, posters, capture metadata, frame sequences and run-specific observations are stored under `logs/studio/<job>/captures/<run>/`. Browser endpoints allow only the current recording's registered scenes and known output files. Video serving supports byte ranges for seeking. Encoding failures keep source frames and physics observations. No synthetic frames or substitute movies are generated in production.

API reference: https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/AutomationLibrary

Encoder reference: https://github.com/imageio/imageio-ffmpeg

## Verification boundary

- Full backend suite, production frontend build, ESLint and targeted Python lint.
- Real FFmpeg encoding and decoding of explicitly synthetic test frames; timing and distinct output frames verified.
- API checks for playable media, byte-range requests, and rejected unregistered files/scenes.
- Fake-editor protocol verifies one input, frame capture completion, measured movement/quiet state, observations and simulation stop. The pre-existing no-input Chaos protocol is retained and tested.
- Browser fixture test loads, plays, pauses and downloads MP4 and checks desktop/mobile layout and JavaScript errors. Fixtures are marked as fixtures, not Unreal evidence.
- Actual Unreal 5.8 screenshot capture during simulation is the next user-side test. The confirmed previous live Chaos workflow is evidence for the base bridge, not proof of the new capture API behavior.

Next: verify the first real clips on Andy's PC, then improve camera framing/capture smoothness from actual output. General ARC asset generation/repair and live Unreal streaming remain separate work.
