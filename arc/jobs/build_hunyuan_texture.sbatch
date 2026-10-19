#!/bin/bash
#SBATCH --job-name=emergency-poc-hunyuan-texture-build
#SBATCH --time=02:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --gres=gpu:1
#SBATCH --output=arc/results/hunyuan-texture-build-%j.out
#SBATCH --error=arc/results/hunyuan-texture-build-%j.err
set -euo pipefail
source arc/scripts/load_arc_config.sh
source arc/scripts/hunyuan_texture_config.sh
module load apptainer
export APPTAINER_CACHEDIR="$ARC_PROJECT_WORKSPACE/cache/apptainer"
export APPTAINER_TMPDIR="$ARC_PROJECT_WORKSPACE/cache/apptainer-tmp"
mkdir -p "$ARC_HUNYUAN_ROOT/metadata" "$ARC_HUNYUAN_ROOT/cache/texture-pip" "$ARC_HUNYUAN_ROOT/tmp/texture"
paint_source="$ARC_HUNYUAN_ROOT/texture-source"
if [[ ! -d "$paint_source/.git" ]]; then
  git clone --no-hardlinks "$ARC_HUNYUAN_ROOT/source" "$paint_source"
fi
[[ "$(git -C "$paint_source" rev-parse HEAD)" == "$ARC_HUNYUAN_SOURCE_REVISION" ]] || { echo "Unexpected paint source revision" >&2; exit 2; }
rm -f "$ARC_HUNYUAN_ROOT/metadata/texture-ready.env"
apptainer exec --nv --bind "$ARC_PROJECT_WORKSPACE:/workspace" --bind "$PWD:/project" "$ARC_HUNYUAN_CONTAINER" /bin/bash -lc '
  set -euo pipefail
  export HOME=/workspace/hunyuan21/home
  export TMPDIR=/workspace/hunyuan21/tmp/texture
  export PIP_CACHE_DIR=/workspace/hunyuan21/cache/texture-pip
  export CUDA_HOME=/usr/local/cuda
  export MAX_JOBS=8
  export TORCH_CUDA_ARCH_LIST=8.0
  export PYTHONPATH=/project/arc/scripts:/workspace/hunyuan21/texture-source/hy3dpaint:/workspace/hunyuan21/texture-source/hy3dshape
  export LD_LIBRARY_PATH=/workspace/hunyuan21/texture-environment/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
  source /opt/conda/etc/profile.d/conda.sh
  if [[ ! -x /workspace/hunyuan21/texture-environment/bin/python ]]; then
    conda create -y -p /workspace/hunyuan21/texture-environment --clone /workspace/hunyuan21/environment
  fi
  conda activate /workspace/hunyuan21/texture-environment
  python -m pip install setuptools==75.8.2 wheel
  python -m pip install --no-build-isolation -r /project/arc/requirements-hunyuan-texture.txt
  python /project/arc/scripts/patch_hunyuan_texture_source.py /workspace/hunyuan21/texture-source
  cd /workspace/hunyuan21/texture-source
  python -m pip install ./hy3dpaint/custom_rasterizer --no-build-isolation
  cd hy3dpaint/DifferentiableRenderer
  bash compile_mesh_painter.sh
  python -m pip check
  python -c "from hunyuan_texture_compat import install_torchvision_compat; install_torchvision_compat(); import torch, custom_rasterizer; from textureGenPipeline import Hunyuan3DPaintPipeline; from hunyuanpaintpbr.unet.modules import Dino_v2; from realesrgan import RealESRGANer; from DifferentiableRenderer.mesh_inpaint_processor import meshVerticeInpaint; assert torch.cuda.is_available(); print(torch.cuda.get_device_name(0)); print(\"Hunyuan texture imports and CUDA: OK\")"
  python -m pip freeze > /workspace/hunyuan21/metadata/texture-requirements.freeze.txt
'
mkdir -p "$ARC_HUNYUAN_ROOT/texture-weights"
esrgan="$ARC_HUNYUAN_ROOT/texture-weights/RealESRGAN_x4plus.pth"
if [[ ! -s "$esrgan" ]]; then
  curl --fail --location --retry 3 --output "$esrgan.part" "$ARC_HUNYUAN_ESRGAN_URL"
  mv "$esrgan.part" "$esrgan"
fi
git -C "$paint_source" diff > "$ARC_HUNYUAN_ROOT/metadata/texture-source-patches.diff"
{
  echo "source_revision=$ARC_HUNYUAN_SOURCE_REVISION"
  echo "build_job_id=$SLURM_JOB_ID"
  echo "esrgan_sha256=$(sha256sum "$esrgan" | cut -d ' ' -f 1)"
  date --iso-8601=seconds
} > "$ARC_HUNYUAN_ROOT/metadata/texture-ready.env"
echo "Texture runtime ready: $ARC_HUNYUAN_ROOT/metadata/texture-ready.env"
