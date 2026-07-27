#!/bin/bash
#SBATCH --job-name=emergency-poc-cpu-check
#SBATCH --account=research-mel
#SBATCH --partition=normal_q
#SBATCH --time=00:02:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --output=arc/results/cpu-check-%j.out
#SBATCH --error=arc/results/cpu-check-%j.err

set -euo pipefail

echo "VT ARC CPU checkout"
echo "Account: ${SLURM_JOB_ACCOUNT:-not reported}"
echo "Partition: ${SLURM_JOB_PARTITION:-not reported}"
echo "Job ID: ${SLURM_JOB_ID:-not reported}"
echo "Node: $(hostname)"
echo "Time: $(date --iso-8601=seconds)"
echo "CPU count: ${SLURM_CPUS_PER_TASK:-not reported}"
python --version 2>&1 || true
uname -a
