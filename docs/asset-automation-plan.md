# Natural-language assets and frontend ARC jobs

**October 26 update:** this bounded asset lane is implemented, including a real
Blender MCP preparation worker. Read `docs/asset-automation-runbook.md` for setup
and `docs/arc-handoff-2026-10-26.md` for exact validation/live-run status. The design
discussion below is retained as history; the image provider is now pinned SDXL
on ARC. SSH setup and first actual GPU/Unreal integration runs remain pending.

## Requested outcome, October 19, 2026

Andy wants to test the first couch through the intended automated workflow:
describe the design, generate its reference and 3D geometry, retrieve the result,
and prepare a separate Blender review file from the frontend. Resolve the seven
existing PRs before implementing this next batch. No couch GPU job has run yet.

The existing saved request is `64e106d0434281a2a919e2d7e7706dd8a17d18f48b5f9be767a185fa7a55ce52`:
charcoal two-seat couch, target dimensions 1.8 x 0.85 x 0.85 m, seed 42. Its
reference was prepared previously. It can test remote transport, but it does not
test a new description-to-image stage. Keep it as a baseline.

## Bounded next implementation

1. Use the local backend as the ARC connection owner. Use Windows OpenSSH and a
   user-configured host alias with a passphrase-protected key unlocked in the
   user's SSH agent. Require normal host verification and VPN off campus. Do not
   collect VT passwords, Duo codes, private keys or passphrases in the frontend.
   Do not create keys or change server access without a separate explicit setup
   action. Keep Open OnDemand available for setup and recovery.
2. Add a connection check, fixed request upload, job submission, status polling
   and result retrieval. Keep all model computation in Slurm jobs. Use bounded
   short SSH commands; do not install a frontend service on the login node. The
   browser must never supply arbitrary shell commands or remote paths. Keep the
   existing request identity, result checksums and provenance validation.
3. Persist dispatch state before submission. Record job IDs and recover ambiguous
   network failures by querying the saved request/job identity instead of blindly
   resubmitting. Permit one asset generation at a time for this POC. A completed
   Slurm state alone is not a validated model: retrieve and validate its package.
4. Add a real description-to-reference-image provider before Hunyuan generation.
   Provider/model selection remains to be verified: either an ARC GPU image model
   with suitable access/runtime/license, or a separately configured image API.
   The existing hosted ARC chat key does not establish access to image generation
   or GPU submission. The assistant's image-generation tool is not an endpoint the
   local app can call. Do not substitute a fixed reference for a fresh design.
5. Preserve the prompt, image model/settings and actual reference bytes. Compute
   the final immutable furniture identity using those bytes and existing design
   settings; keep its link to the initial natural-language request. Reuse saved
   outputs without claiming bitwise regeneration. Retrieve the real GLB, prepare
   the Blender copy and show actual dimensions and failure/retry status.

## Whole-room endpoint

Room structure can continue to be generated procedurally from validated spatial
plans. Furniture should remain separate objects with reusable reviewed designs.
Mixed-asset planning, footprint checks, Blender bindings and Unreal bindings must
be extended together. A missing couch must not be represented by a chair. Inspect
the actual new mesh and prepare suitable collision pieces before room simulation.
Automatic transport and visual plausibility do not establish physical accuracy.

## Acceptance

One new couch description produces an actual new reference, one recorded ARC job,
a validated returned model and a separate editable Blender review copy from the
frontend, with no manual ZIP roundtrip. Verify a failed connection and an
interrupted/reconnected submission without duplicate GPU work. Existing reviewed
chair rooms, private configuration and saved evidence remain available.

Official access guidance reviewed October 19, 2026:

- https://www.docs.arc.vt.edu/usage/sshkeys.html
- https://docs.arc.vt.edu/usage/abuse.html
- https://www.docs.arc.vt.edu/usage/vscode_remote_ssh.html

SSH and Slurm are documented access routes. A VT-provided public Slurm REST API
has not been established by this review; do not assume such an endpoint exists.
