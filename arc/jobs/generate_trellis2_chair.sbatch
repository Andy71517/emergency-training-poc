#!/bin/bash
#SBATCH --job-name=emergency-poc-chair
#SBATCH --time=02:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=96G
#SBATCH --gres=gpu:1
#SBATCH --output=arc/results/trellis2-chair-%j.out
#SBATCH --error=arc/results/trellis2-chair-%j.err

set -euo pipefail
source arc/scripts/load_arc_config.sh

runtime_root="$ARC_PROJECT_WORKSPACE/trellis2"
input="$runtime_root/inputs/wooden-chair.png"
output="$runtime_root/outputs/wooden-chair-${SLURM_JOB_ID}"
container="$ARC_PROJECT_WORKSPACE/containers/trellis2-pytorch-2.6.0-cu124.sif"
if [[ ! -f "$input" || ! -f "$container" || ! -x "$runtime_root/environment/bin/python" ]]; then
  echo "Missing input image or TRELLIS runtime. Expected image at $input" >&2
  exit 2
fi
mkdir -p "$output" "$ARC_PROJECT_WORKSPACE/cache/huggingface" "$ARC_PROJECT_WORKSPACE/cache/apptainer" "$ARC_PROJECT_WORKSPACE/cache/apptainer-tmp"
export APPTAINER_CACHEDIR="$ARC_PROJECT_WORKSPACE/cache/apptainer"
export APPTAINER_TMPDIR="$ARC_PROJECT_WORKSPACE/cache/apptainer-tmp"
export TRELLIS_SOURCE_REVISION
TRELLIS_SOURCE_REVISION=$(git -C "$runtime_root/source" rev-parse HEAD)
module load apptainer
echo "Output: $output"
echo "Source revision: $TRELLIS_SOURCE_REVISION"

apptainer exec --nv --bind "$ARC_PROJECT_WORKSPACE:/workspace" --bind "$PWD:/project" "$container" /bin/bash -lc '
  set -euo pipefail
  export HOME=/workspace/trellis2/home
  export HF_HOME=/workspace/cache/huggingface
  export OPENCV_IO_ENABLE_OPENEXR=1
  export PYTHONPATH=/workspace/trellis2/source${PYTHONPATH:+:$PYTHONPATH}
  source /opt/conda/etc/profile.d/conda.sh
  conda activate /workspace/trellis2/environment
  cd /workspace/trellis2/source
  python /project/arc/scripts/generate_trellis2_asset.py \
    --image /workspace/trellis2/inputs/wooden-chair.png \
    --output "/workspace/trellis2/outputs/wooden-chair-${SLURM_JOB_ID}"
'
