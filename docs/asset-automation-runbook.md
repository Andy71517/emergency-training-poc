# Description to Blender and Unreal package

The Asset library now has **Describe it. Build it.** One description creates a
reference on ARC with pinned SDXL 1.0, then runs the existing Hunyuan shape/paint
lane. The backend retrieves and validates the package, and a real stdio MCP client
calls the local Blender preparation server. There is no third-party Blender
add-on or arbitrary Python-execution tool to install.

Blender saves an editable `furniture-unreal.blend`, a preview, preparation report
and `unreal-package.zip`. The package includes FBX, source texture bytes, explicit
PBR wiring, provenance/notices and an Unreal 5.8 import script. Unreal imports FBX;
the `.blend` is the editable source. Visual/collision fit and actual engine cooking
still require verification. This is not a certification of physical accuracy.

## 1. One-time ARC connection setup

Connect to VT VPN off campus. In your own PowerShell, first establish normal SSH
access to `anirudhalledula@tinkercliffs2.arc.vt.edu`. Verify the host fingerprint
through VT's trusted documentation/support before accepting a new host key. Never
disable host checking. Password/Duo entry stays in your terminal, never this app
or chat.

The October 26 check failed with **no known ED25519 host key**, so unattended
submission has not yet been verified on this computer. No credentials or trusted
hosts were changed by the implementation.

For repeat access, use a passphrase-protected key and the Windows OpenSSH agent.
If you already have an approved key, reuse it. Otherwise, follow VT's instructions
to create one and install only its public part on ARC. A possible new-key command
(choose a new filename; do not overwrite an existing key) is:

```powershell
ssh-keygen -t ed25519 -f "$env:USERPROFILE\.ssh\fieldwork_arc"
```

Enter a strong passphrase locally. Add the `.pub` contents to your ARC account's
`~/.ssh/authorized_keys` using your authenticated session; follow VT's file
permission instructions. Unlock the private key locally with:

```powershell
ssh-add "$env:USERPROFILE\.ssh\fieldwork_arc"
ssh -o BatchMode=yes -o StrictHostKeyChecking=yes anirudhalledula@tinkercliffs2.arc.vt.edu true
```

The final command must exit successfully without asking for input. If `ssh-add`
cannot reach the Windows OpenSSH agent, enable/start that service using your
normal Windows administration process, then retry. The app will not silently
fall back to passwords or weaken verification. Open OnDemand remains useful for
initial key setup and recovery; it is not required for each job after this setup.

Official guidance: https://www.docs.arc.vt.edu/usage/sshkeys.html and
https://docs.arc.vt.edu/usage/abuse.html .

## 2. Update the ARC worker once

In your existing authenticated ARC shell, inspect status before changing branches:

```bash
cd "$HOME/emergency-training-poc"
git status --short --branch
git fetch origin
git switch main
git pull --ff-only
```

If there are changed tracked files or a switch/update fails, stop rather than
discarding changes. Keep ignored `arc/.env` and all model/output storage. New files
are `remote_asset_control.sh/.py` and `generate_automated_furniture.sbatch`.
The existing shape/texture runtime markers must be present. No runtime rebuild is
planned: SDXL uses the existing shape environment's Diffusers/Torch packages.
Its **first live import/model run is still an integration checkpoint**. First use
downloads public model files into the existing cache on the allocated GPU node;
no large model or inference process runs on the login node.

## 3. Configure the local backend

Preserve the existing private `backend/.env`. Add only these non-secret settings:

```dotenv
ARC_SSH_TARGET=anirudhalledula@tinkercliffs2.arc.vt.edu
ARC_REMOTE_REPO=/home/anirudhalledula/emergency-training-poc
```

An existing verified SSH alias also works. Keep `BLENDER_EXECUTABLE` configured;
the backend checks that this executable exists before starting new generation.
No key contents, passphrase, password or Duo code belongs in this file. The hosted
ARC chat key is separate and does not grant SSH/GPU access.

After updating local sources, install their declared MCP/CPU collision tools,
build the frontend and restart the single local backend:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
npm.cmd --prefix web ci
npm.cmd --prefix web run build
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8772
```

## 4. Run the couch from the app

1. Open **Asset library**. Use **Check ARC connection**. It confirms worker
   connectivity and existing runtime markers, not successful new model inference.
2. Enter the couch description and target dimensions, then **Generate & prepare**.
   No manual reference upload or request/result ZIP roundtrip is needed.
3. The saved dispatch shows a Slurm ID only after submission evidence exists.
   Phases are image, shape and texture. Allocation usage applies; initial model
   downloads and queue time can dominate the first run.
4. If a connection drops, use **Reconnect / resume same job**. Never start a second
   dispatch just because the SSH response was lost. The remote journal and Slurm
   comment support recovery. Unknown submission remains unknown until evidence
   resolves it; no automatic duplicate submission occurs.
5. Open the generated design. Download the Blender file and Unreal package and
   inspect the whole result. A known terminal ARC failure allows an explicit new
   attempt. Imported geometry is kept even if Blender preparation fails; retry
   preparation on the design card without regenerating the model.

The older saved reference-only couch remains a separate baseline. A new prompt
run must generate a real new reference; it does not silently use that baseline.
Exact prompts reuse their saved job; changing the seed/design requests a new one.

## 5. What Blender automates

The MCP server exposes only `inspect_asset` and `prepare_asset`, scoped to this
library's IDs. It runs trusted scripts in background Blender, keeps the input GLB
unchanged and preserves the imported source in a hidden collection. It minimally
welds coincident vertices, dissolves collapsed geometry, recalculates normals,
matches height uniformly and grounds/centers the working copy. Source UVs and
materials remain on the render mesh.

A separate CPU process uses pinned CoACD with a 2 cm approximation threshold,
at most 32 hulls and 64 vertices per hull. Hulls must be closed, convex, have
positive volumes and stay near the source bounds. They are named `UCX_SM_Asset_*`.
These are proxies, not inferred physical parts. Automatic cleanup does not invent
missing legs, reopen arbitrary fused gaps or guarantee topology/structural repair.
Review the reported dimensions, open spaces and foot/contact fit.

FBX export selects only `SM_Asset` and its UCX hulls. A Blender reimport checks
mesh/hull counts, bounds, UV layer and material-slot preservation. Temporary
verification images/materials are removed so they do not contaminate packed
source textures. The `.blend` packs its textures. The ZIP retains original image
bytes, channel/factor instructions, notices, image/shape/paint provenance and hashes.

On a preparation failure, inspect
`logs/studio/asset-library/ASSET_ID/blender/RUN_ID/worker.log` locally. The render
source and intermediate cleanup/decomposition files remain available. Native
workers have bounded timeouts; they do not read the MCP transport's input stream.

## 6. Unreal import and remaining boundary

Extract `unreal-package.zip`. With Unreal 5.8's Python Editor Script Plugin enabled,
execute `import_furniture_package.py` from that folder. It verifies hashes, creates
fresh content, imports the explicit UCX hulls, verifies size/count and wires
supported base-color/roughness/metallic/normal maps and factors. It preserves the
current map and starts no physics. Unsupported material mappings stop for review.
Reports are written under the project `Saved/FIELDWORK` directory.

The generic importer has preflight/compile checks but **has not yet run in Unreal**.
First engine import, collision cooking, contact stability and the actual couch's
visual fit remain live checks. Existing chair rooms keep their reviewed binding;
mixed-furniture room planning/Blender/Unreal bindings remain a separate coordinated
extension. This batch automates asset preparation, not arbitrary whole-scene
semantic repair or validated emergency/evacuation simulation.

## Evidence for this batch

- Real MCP handshake/tool calls and real Blender 5.1.2 preparation executed on an
  explicitly synthetic furniture fixture, not a substitute ARC couch result.
- Native cleanup, CoACD, 28 convex pieces, packed textures, preview, `.blend`, FBX
  reimport and package/hash validation succeeded on that fixture.
- Focused and full offline tests exercise journal recovery, duplicate suppression,
  prompt/model binding, worker failures, path/origin/credential boundaries and
  package validation. Exact final test totals are recorded in the handoff.
- No live ARC image/shape/paint job or new Unreal runtime was executed here. The
  SSH setup above is required before the first actual automated couch run.

Model: https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0
Collision library: https://github.com/SarahWeiii/CoACD
MCP SDK: https://github.com/modelcontextprotocol/python-sdk/tree/v1.x
