#!/bin/bash
#SBATCH --job-name=emergency-poc-hunyuan-chair
#SBATCH --time=02:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --gres=gpu:1
#SBATCH --output=arc/results/hunyuan-chair-%j.out
#SBATCH --error=arc/results/hunyuan-chair-%j.err
set -euo pipefail
source arc/scripts/load_arc_config.sh
source arc/scripts/hunyuan_config.sh
output="$ARC_HUNYUAN_ROOT/outputs/wooden-chair-$SLURM_JOB_ID"
mkdir -p "$output" "$ARC_HUNYUAN_ROOT/inputs"
cp "$ARC_HUNYUAN_INPUT" "$ARC_HUNYUAN_ROOT/inputs/wooden-chair.png"
export APPTAINER_CACHEDIR="$ARC_PROJECT_WORKSPACE/cache/apptainer"
export APPTAINER_TMPDIR="$ARC_PROJECT_WORKSPACE/cache/apptainer-tmp"
export HUNYUAN_SOURCE_REVISION="$ARC_HUNYUAN_SOURCE_REVISION"
export HUNYUAN_MODEL_REVISION="$ARC_HUNYUAN_MODEL_REVISION"
module load apptainer
echo "Output: $output"
apptainer exec --nv --bind "$ARC_PROJECT_WORKSPACE:/workspace" --bind "$PWD:/project" "$ARC_HUNYUAN_CONTAINER" /bin/bash -lc '
  set -euo pipefail
  export HOME=/workspace/hunyuan21/home
  export TMPDIR=/workspace/hunyuan21/tmp
  export HF_HOME=/workspace/hunyuan21/cache/huggingface
  export U2NET_HOME=/workspace/hunyuan21/cache/rembg
  export PYTHONPATH=/workspace/hunyuan21/source/hy3dshape
  export LD_LIBRARY_PATH=/workspace/hunyuan21/environment/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
  source /opt/conda/etc/profile.d/conda.sh
  conda activate /workspace/hunyuan21/environment
  cd /workspace/hunyuan21/source
  python -u /project/arc/scripts/generate_hunyuan_asset.py \
    --image /workspace/hunyuan21/inputs/wooden-chair.png \
    --output "/workspace/hunyuan21/outputs/wooden-chair-${SLURM_JOB_ID}"
'
