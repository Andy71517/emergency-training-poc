#!/bin/bash
#SBATCH --job-name=emergency-poc-a100-check
#SBATCH --account=research-mel
#SBATCH --partition=a100_normal_q
#SBATCH --time=00:05:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --gres=gpu:1
#SBATCH --output=arc/results/a100-check-%j.out
#SBATCH --error=arc/results/a100-check-%j.err

set -euo pipefail

echo "VT ARC A100 checkout"
echo "Account: ${SLURM_JOB_ACCOUNT:-not reported}"
echo "Partition: ${SLURM_JOB_PARTITION:-not reported}"
echo "Job ID: ${SLURM_JOB_ID:-not reported}"
echo "Node: $(hostname)"
echo "Time: $(date --iso-8601=seconds)"
echo "Assigned GPUs: ${CUDA_VISIBLE_DEVICES:-not reported}"
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv
