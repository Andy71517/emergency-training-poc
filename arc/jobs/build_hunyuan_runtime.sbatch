#!/bin/bash
#SBATCH --job-name=emergency-poc-hunyuan-build
#SBATCH --time=01:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --gres=gpu:1
#SBATCH --output=arc/results/hunyuan-build-%j.out
#SBATCH --error=arc/results/hunyuan-build-%j.err
set -euo pipefail
source arc/scripts/load_arc_config.sh
source arc/scripts/hunyuan_config.sh
mkdir -p "$ARC_HUNYUAN_ROOT/metadata" "$ARC_HUNYUAN_ROOT/home" "$ARC_HUNYUAN_ROOT/tmp" "$ARC_HUNYUAN_ROOT/cache"
export APPTAINER_CACHEDIR="$ARC_PROJECT_WORKSPACE/cache/apptainer"
export APPTAINER_TMPDIR="$ARC_PROJECT_WORKSPACE/cache/apptainer-tmp"
module load apptainer
source_dir="$ARC_HUNYUAN_ROOT/source"
if [[ ! -d "$source_dir/.git" ]]; then
  git clone https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1.git "$source_dir"
fi
git -C "$source_dir" fetch origin "$ARC_HUNYUAN_SOURCE_REVISION"
git -C "$source_dir" checkout --detach "$ARC_HUNYUAN_SOURCE_REVISION"
# Remove the ready marker until all imports and CUDA checks pass again.
rm -f "$ARC_HUNYUAN_ROOT/metadata/runtime-ready.env"
apptainer exec --nv --bind "$ARC_PROJECT_WORKSPACE:/workspace" --bind "$PWD:/project" "$ARC_HUNYUAN_CONTAINER" /bin/bash -lc '
  set -euo pipefail
  export HOME=/workspace/hunyuan21/home
  export TMPDIR=/workspace/hunyuan21/tmp
  export PIP_CACHE_DIR=/workspace/hunyuan21/cache/pip
  export PYTHONPATH=/workspace/hunyuan21/source/hy3dshape
  export LD_LIBRARY_PATH=/workspace/hunyuan21/environment/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
  source /opt/conda/etc/profile.d/conda.sh
  if [[ ! -x /workspace/hunyuan21/environment/bin/python ]]; then
    conda create -y -p /workspace/hunyuan21/environment python=3.10 pip
  fi
  conda activate /workspace/hunyuan21/environment
  conda install -y -c conda-forge libgl libglib
  python -m pip install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cu124
  python -m pip install -r /project/arc/requirements-hunyuan-shape.txt
  python -m pip check
  python -c "import torch; from hy3dshape.pipelines import Hunyuan3DDiTFlowMatchingPipeline; from hy3dshape.rembg import BackgroundRemover; from hy3dshape.postprocessors import FaceReducer; assert torch.cuda.is_available(); print(torch.__version__); print(torch.cuda.get_device_name(0)); print(\"Hunyuan shape imports and CUDA: OK\")"
  python -m pip freeze > /workspace/hunyuan21/metadata/requirements.freeze.txt
'
{
  echo "source_revision=$ARC_HUNYUAN_SOURCE_REVISION"
  echo "container_sha256=$(sha256sum "$ARC_HUNYUAN_CONTAINER" | cut -d ' ' -f 1)"
  echo "build_job_id=$SLURM_JOB_ID"
  date --iso-8601=seconds
} > "$ARC_HUNYUAN_ROOT/metadata/runtime-ready.env"
cp "$ARC_HUNYUAN_ROOT/metadata/runtime-ready.env" "$ARC_HUNYUAN_ROOT/metadata/runtime-build-${SLURM_JOB_ID}.env"
echo "Hunyuan runtime ready: $ARC_HUNYUAN_ROOT/metadata/runtime-ready.env"
