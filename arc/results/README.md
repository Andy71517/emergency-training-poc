# Sanitized VT ARC results

Keep short, dated verification notes here. Do not commit raw scheduler output,
usernames, node names, credentials, tokens, private keys, or other sensitive
environment details.

Suggested format:

```text
Date:
CPU job ID:
CPU result:
GPU job ID:
GPU model:
GPU result:
Project storage access:
Follow-up:
```

## 2026-08-31 A100 and Apptainer gate

- Project storage access: passed for the configured `research-mel` workspace.
- A100 checkout: passed; the requested account and `a100_normal_q` completed
  successfully with one NVIDIA A100 80 GB GPU.
- Apptainer runtime: passed on an allocated A100 compute node using
  `apptainer --nv` and a project-stored Alpine smoke image.
- Follow-up: build the pinned TRELLIS.2 environment before downloading model
  weights or generating a chair candidate.
