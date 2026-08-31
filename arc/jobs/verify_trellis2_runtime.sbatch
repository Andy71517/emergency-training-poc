#!/bin/bash
#SBATCH --job-name=emergency-poc-trellis2-check
#SBATCH --time=00:10:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --gres=gpu:1
#SBATCH --output=arc/results/trellis2-check-%j.out
#SBATCH --error=arc/results/trellis2-check-%j.err

set -euo pipefail
source arc/scripts/load_arc_config.sh

runtime_root="$ARC_PROJECT_WORKSPACE/trellis2"
environment_dir="$runtime_root/environment"
container_image="$ARC_PROJECT_WORKSPACE/containers/trellis2-pytorch-2.6.0-cu124.sif"

if [[ ! -x "$environment_dir/bin/python" || ! -f "$container_image" ]]; then
  echo "TRELLIS.2 runtime is not built. Submit arc/scripts/submit_trellis2_build.sh first." >&2
  exit 2
fi

module load apptainer
echo "VT ARC TRELLIS.2 runtime check"
echo "Job ID: ${SLURM_JOB_ID:-not reported}"
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv

apptainer exec --nv --bind "$ARC_PROJECT_WORKSPACE:/workspace" "$container_image" /bin/bash -lc '
  set -euo pipefail
  source /opt/conda/etc/profile.d/conda.sh
  conda activate /workspace/trellis2/environment
  cd /workspace/trellis2/source
  python -c "import torch, trellis2, o_voxel; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0)); print(trellis2.__file__); print(o_voxel.__file__)"
'
