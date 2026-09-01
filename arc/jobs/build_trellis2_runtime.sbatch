#!/bin/bash
#SBATCH --job-name=emergency-poc-trellis2-build
#SBATCH --time=03:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=96G
#SBATCH --gres=gpu:1
#SBATCH --output=arc/results/trellis2-build-%j.out
#SBATCH --error=arc/results/trellis2-build-%j.err

# Build the software runtime only. Model weights are deliberately excluded:
# their download and license acceptance need a separate approval and record.
set -euo pipefail

source arc/scripts/load_arc_config.sh

for variable_name in ARC_TRELLIS2_REPOSITORY ARC_TRELLIS2_REVISION ARC_TRELLIS2_CONTAINER_IMAGE; do
  if [[ -z "${!variable_name:-}" ]]; then
    echo "$variable_name is required in arc/.env before building TRELLIS.2." >&2
    exit 2
  fi
done

runtime_root="$ARC_PROJECT_WORKSPACE/trellis2"
source_dir="$runtime_root/source"
container_dir="$ARC_PROJECT_WORKSPACE/containers"
container_image="$container_dir/trellis2-pytorch-2.6.0-cu124.sif"
metadata_dir="$runtime_root/metadata"
export APPTAINER_CACHEDIR="$ARC_PROJECT_WORKSPACE/cache/apptainer"
export APPTAINER_TMPDIR="$ARC_PROJECT_WORKSPACE/cache/apptainer-tmp"

mkdir -p "$runtime_root" "$container_dir" "$APPTAINER_CACHEDIR" "$APPTAINER_TMPDIR" "$metadata_dir"
module load apptainer

echo "VT ARC TRELLIS.2 runtime build"
echo "Account: ${SLURM_JOB_ACCOUNT:-not reported}"
echo "Partition: ${SLURM_JOB_PARTITION:-not reported}"
echo "Job ID: ${SLURM_JOB_ID:-not reported}"
echo "Repository: $ARC_TRELLIS2_REPOSITORY"
echo "Revision: $ARC_TRELLIS2_REVISION"
echo "Container source: $ARC_TRELLIS2_CONTAINER_IMAGE"
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv

if [[ ! -d "$source_dir/.git" ]]; then
  git clone --recursive "$ARC_TRELLIS2_REPOSITORY" "$source_dir"
fi
git -C "$source_dir" fetch --tags origin
git -C "$source_dir" checkout --detach "$ARC_TRELLIS2_REVISION"
git -C "$source_dir" submodule update --init --recursive

if [[ ! -f "$container_image" ]]; then
  apptainer pull "$container_image" "$ARC_TRELLIS2_CONTAINER_IMAGE"
fi

# Upstream's setup script assumes sudo for a system package. The CUDA development
# image provides that dependency, so reproduce only its Python/CUDA steps here.
apptainer exec --nv --bind "$ARC_PROJECT_WORKSPACE:/workspace" "$container_image" /bin/bash -lc '
  set -euo pipefail
  export HOME=/workspace/trellis2/home
  export PIP_CACHE_DIR=/workspace/cache/pip
  export CUDA_HOME=/usr/local/cuda
  mkdir -p "$HOME" "$PIP_CACHE_DIR"
  source /opt/conda/etc/profile.d/conda.sh
  if [[ ! -x /workspace/trellis2/environment/bin/python ]]; then
    conda create -y -p /workspace/trellis2/environment python=3.10 pip
  fi
  conda activate /workspace/trellis2/environment
  # The upstream setup uses Git for pinned sources; the CUDA image does not guarantee it.
  conda install -y git
  python -m pip install --upgrade pip
  python -m pip install torch==2.6.0 torchvision==0.21.0 --index-url https://download.pytorch.org/whl/cu124
  python -m pip install imageio imageio-ffmpeg tqdm easydict opencv-python-headless ninja trimesh transformers gradio==6.0.1 tensorboard pandas lpips zstandard kornia timm pillow-simd
  python -m pip install git+https://github.com/EasternJournalist/utils3d.git@9a4eb15e4021b67b12c460c7057d642626897ec8
  python -m pip install flash-attn==2.7.3 --no-build-isolation
  rm -rf /tmp/trellis2-extensions
  mkdir -p /tmp/trellis2-extensions
  git clone -b v0.4.0 https://github.com/NVlabs/nvdiffrast.git /tmp/trellis2-extensions/nvdiffrast
  python -m pip install /tmp/trellis2-extensions/nvdiffrast --no-build-isolation
  git clone -b renderutils https://github.com/JeffreyXiang/nvdiffrec.git /tmp/trellis2-extensions/nvdiffrec
  python -m pip install /tmp/trellis2-extensions/nvdiffrec --no-build-isolation
  git clone --recursive https://github.com/JeffreyXiang/CuMesh.git /tmp/trellis2-extensions/CuMesh
  python -m pip install /tmp/trellis2-extensions/CuMesh --no-build-isolation
  git clone --recursive https://github.com/JeffreyXiang/FlexGEMM.git /tmp/trellis2-extensions/FlexGEMM
  python -m pip install /tmp/trellis2-extensions/FlexGEMM --no-build-isolation
  cp -r /workspace/trellis2/source/o-voxel /tmp/trellis2-extensions/o-voxel
  python -m pip install /tmp/trellis2-extensions/o-voxel --no-build-isolation
  python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
'

{
  echo "source_repository=$ARC_TRELLIS2_REPOSITORY"
  echo "source_revision=$(git -C "$source_dir" rev-parse HEAD)"
  echo "source_status=$(git -C "$source_dir" status --porcelain | wc -l | tr -d " ")"
  echo "container_source=$ARC_TRELLIS2_CONTAINER_IMAGE"
  echo "container_sha256=$(sha256sum "$container_image" | awk "{print \$1}")"
  echo "environment_dir=$runtime_root/environment"
  echo "build_job_id=${SLURM_JOB_ID:-not reported}"
  date --iso-8601=seconds
} > "$metadata_dir/runtime-build-${SLURM_JOB_ID}.env"

echo "Runtime metadata: $metadata_dir/runtime-build-${SLURM_JOB_ID}.env"
