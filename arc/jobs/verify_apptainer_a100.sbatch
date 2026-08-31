#!/bin/bash
#SBATCH --job-name=emergency-poc-apptainer-check
#SBATCH --time=00:05:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --gres=gpu:1
#SBATCH --output=arc/results/apptainer-check-%j.out
#SBATCH --error=arc/results/apptainer-check-%j.err

set -euo pipefail

# Submit from the repository root so the ignored local ARC configuration is available.
source arc/scripts/load_arc_config.sh

export APPTAINER_CACHEDIR="$ARC_PROJECT_WORKSPACE/cache/apptainer"
smoke_image="$ARC_PROJECT_WORKSPACE/containers/apptainer-smoke-alpine-3.20.sif"

mkdir -p "$ARC_PROJECT_WORKSPACE/containers" "$APPTAINER_CACHEDIR"

module load apptainer

echo "VT ARC Apptainer A100 checkout"
echo "Account: ${SLURM_JOB_ACCOUNT:-not reported}"
echo "Partition: ${SLURM_JOB_PARTITION:-not reported}"
echo "Job ID: ${SLURM_JOB_ID:-not reported}"
echo "Apptainer cache: $APPTAINER_CACHEDIR"
apptainer --version
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv

if [[ ! -f "$smoke_image" ]]; then
  apptainer pull "$smoke_image" docker://alpine:3.20
fi

apptainer exec --nv "$smoke_image" /bin/sh -c 'echo "Apptainer GPU smoke test passed"'
sha256sum "$smoke_image"
