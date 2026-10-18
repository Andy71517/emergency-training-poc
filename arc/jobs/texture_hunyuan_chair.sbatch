#!/bin/bash
#SBATCH --job-name=emergency-poc-hunyuan-paint
#SBATCH --time=02:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --gres=gpu:1
#SBATCH --output=arc/results/hunyuan-paint-%j.out
#SBATCH --error=arc/results/hunyuan-paint-%j.err
set -euo pipefail
source arc/scripts/load_arc_config.sh
source arc/scripts/hunyuan_texture_config.sh
[[ "${HUNYUAN_SHAPE_JOB_ID:-}" =~ ^[0-9]+$ ]] || { echo "Missing source shape job ID" >&2; exit 2; }
export HUNYUAN_PAINT_REVISION="$ARC_HUNYUAN_PAINT_REVISION"
export HUNYUAN_DINO_REVISION="$ARC_HUNYUAN_DINO_REVISION"
export HUNYUAN_TEXTURE_SOURCE_REVISION="$ARC_HUNYUAN_SOURCE_REVISION"
export APPTAINER_CACHEDIR="$ARC_PROJECT_WORKSPACE/cache/apptainer"
export APPTAINER_TMPDIR="$ARC_PROJECT_WORKSPACE/cache/apptainer-tmp"
module load apptainer
echo "Source shape run: $HUNYUAN_SHAPE_JOB_ID"
echo "Output: $ARC_HUNYUAN_ROOT/outputs/wooden-chair-textured-$SLURM_JOB_ID"
apptainer exec --nv --bind "$ARC_PROJECT_WORKSPACE:/workspace" --bind "$PWD:/project" "$ARC_HUNYUAN_CONTAINER" /bin/bash -lc '
  set -euo pipefail
  export HOME=/workspace/hunyuan21/home
  export TMPDIR=/workspace/hunyuan21/tmp/texture
  export HF_HOME=/workspace/hunyuan21/cache/huggingface
  export PYTHONPATH=/project/arc/scripts:/workspace/hunyuan21/texture-source/hy3dpaint:/workspace/hunyuan21/texture-source/hy3dshape
  export LD_LIBRARY_PATH=/workspace/hunyuan21/texture-environment/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
  source /opt/conda/etc/profile.d/conda.sh
  conda activate /workspace/hunyuan21/texture-environment
  cd /workspace/hunyuan21/texture-source
  python -u /project/arc/scripts/paint_hunyuan_asset.py \
    --source "/workspace/hunyuan21/outputs/wooden-chair-${HUNYUAN_SHAPE_JOB_ID}" \
    --output "/workspace/hunyuan21/outputs/wooden-chair-textured-${SLURM_JOB_ID}"
'
