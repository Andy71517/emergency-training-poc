# VT ARC first checkout

This folder is a small, low-cost way to confirm that Andy can use Dr. Cameron's
`research-mel` allocation before this project needs real compute.

These checks do **not** train a model, download model weights, or prove that the
future generation pipeline works. They only answer:

1. Can the account reach TinkerCliffs?
2. Can it read and write inside `/projects/research-mel`?
3. Can Slurm run a tiny CPU job under `research-mel`?
4. Can Slurm allocate one A100 and report its basic hardware details?

## Before the first job

Open a TinkerCliffs shell through ARC Open OnDemand, or connect with the SSH
method in the current ARC documentation. Then run:

```bash
whoami
hostname
quota
sacctmgr show assoc user="$USER" format=Cluster,Account,User,Partition,QOS%50
```

Look for `research-mel` in the association output. Save the command output
without copying credentials, private keys, or access tokens into this repo.

From the repository root on ARC, collect a fuller text snapshot:

```bash
bash arc/scripts/collect_environment.sh
```

## Confirm project-storage access

Use a personal subfolder so the project root stays organized:

```bash
mkdir -p "/projects/research-mel/$USER/emergency-training-poc"
touch "/projects/research-mel/$USER/emergency-training-poc/access-test.txt"
ls -la "/projects/research-mel/$USER/emergency-training-poc"
```

If this fails, keep the exact error and ask Dr. Cameron or ARC support to check
project membership and permissions. Do not work around it with broad
permissions.

## Run the tiny CPU check

Submit from the repository root so the output path resolves correctly:

```bash
sbatch arc/jobs/verify_cpu.sbatch
squeue --me
```

Slurm prints a job number. Replace `JOB_ID` below with that number:

```bash
cat "arc/results/cpu-check-JOB_ID.out"
cat "arc/results/cpu-check-JOB_ID.err"
seff JOB_ID
```

The check passes when the `.out` file shows the expected account, a compute
node hostname, a timestamp, and basic system information, with no meaningful
error in the `.err` file.

## Run the tiny A100 check

Only do this after the CPU check passes:

```bash
sbatch arc/jobs/verify_a100.sbatch
squeue --me
```

After it finishes:

```bash
cat "arc/results/a100-check-JOB_ID.out"
cat "arc/results/a100-check-JOB_ID.err"
seff JOB_ID
```

The check passes when `nvidia-smi` reports an NVIDIA A100 and the assigned Slurm
GPU variable is present. Queue time is not failure; it may simply be waiting
for a GPU.

## What to record

Add a dated, sanitized note to `arc/results/README.md` with:

- CPU and GPU job IDs
- cluster/partition used
- whether project storage worked
- reported GPU model
- failures or warnings worth following up

Raw `.out` and `.err` files are intentionally ignored by Git because they can
contain usernames, node names, or other environment details.

Current ARC references:

- [Getting started](https://www.docs.arc.vt.edu/get_started.html)
- [TinkerCliffs](https://www.docs.arc.vt.edu/resources/compute/00tinkercliffs.html)
- [Slurm overview](https://www.docs.arc.vt.edu/usage/job_scheduling/01_slurm_overview.html)
- [Slurm options](https://www.docs.arc.vt.edu/usage/job_scheduling/02_slurm_options.html)
- [Storage](https://www.docs.arc.vt.edu/resources/storage.html)
- [GPU resources](https://www.docs.arc.vt.edu/resources/gpu.html)
