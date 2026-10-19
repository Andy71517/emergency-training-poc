#!/bin/bash
#SBATCH --job-name=emergency-poc-furniture
#SBATCH --time=02:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --gres=gpu:1
#SBATCH --output=arc/results/hunyuan-variant-%j.out
#SBATCH --error=arc/results/hunyuan-variant-%j.err
set -euo pipefail
source arc/scripts/load_arc_config.sh
source arc/scripts/hunyuan_texture_config.sh
[[ "${HUNYUAN_VARIANT_ID:-}" =~ ^[a-f0-9]{64}$ ]] || { echo 'Missing variant ID.' >&2; exit 2; }
request_dir="$ARC_HUNYUAN_ROOT/requests/$HUNYUAN_VARIANT_ID"
variant_dir="$ARC_HUNYUAN_ROOT/variants/$HUNYUAN_VARIANT_ID"
mkdir -p "$variant_dir"
# Serializes duplicate submissions for this immutable request across cluster nodes.
exec 9>"$variant_dir/generation.lock"
flock -n 9 || { echo 'This exact variant is already generating. No second generation started.'; exit 0; }
[[ ! -f "$variant_dir/result.zip" ]] || { echo "Already generated: $variant_dir/result.zip"; exit 0; }
export HUNYUAN_SOURCE_REVISION="$ARC_HUNYUAN_SOURCE_REVISION"
export HUNYUAN_MODEL_REVISION="$ARC_HUNYUAN_MODEL_REVISION"
export HUNYUAN_PAINT_REVISION="$ARC_HUNYUAN_PAINT_REVISION"
export HUNYUAN_DINO_REVISION="$ARC_HUNYUAN_DINO_REVISION"
export HUNYUAN_TEXTURE_SOURCE_REVISION="$ARC_HUNYUAN_SOURCE_REVISION"
# Avoid exposing the hosted planner credential to GPU processes.
unset ARC_LLM_API_KEY OPENAI_API_KEY HF_TOKEN
export APPTAINER_CACHEDIR="$ARC_PROJECT_WORKSPACE/cache/apptainer"
export APPTAINER_TMPDIR="$ARC_PROJECT_WORKSPACE/cache/apptainer-tmp"
run="$variant_dir/run-$SLURM_JOB_ID"
mkdir -p "$run"
module load apptainer
echo "Variant: $HUNYUAN_VARIANT_ID"
echo "Working output: $run"
apptainer exec --nv --bind "$ARC_PROJECT_WORKSPACE:/workspace" --bind "$PWD:/project" "$ARC_HUNYUAN_CONTAINER" /bin/bash -lc '
  set -euo pipefail
  export HOME=/workspace/hunyuan21/home
  export TMPDIR=/workspace/hunyuan21/tmp
  export HF_HOME=/workspace/hunyuan21/cache/huggingface
  export U2NET_HOME=/workspace/hunyuan21/cache/rembg
  request_dir="/workspace/hunyuan21/requests/$HUNYUAN_VARIANT_ID"
  run="/workspace/hunyuan21/variants/$HUNYUAN_VARIANT_ID/run-$SLURM_JOB_ID"
  source /opt/conda/etc/profile.d/conda.sh
  conda activate /workspace/hunyuan21/environment
  export PYTHONPATH=/workspace/hunyuan21/source/hy3dshape:/project/arc/scripts
  export LD_LIBRARY_PATH=/workspace/hunyuan21/environment/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
  cd /workspace/hunyuan21/source
  # Validate provenance again before consuming GPU time.
  seed=$(python -c "import json; from pathlib import Path; from asset_request import validate_request; p=Path(\"$request_dir\"); r=validate_request(json.loads((p/\"request.json\").read_bytes()), (p/\"reference.png\").read_bytes()); print(r[\"seed\"])")
  python -u /project/arc/scripts/generate_hunyuan_asset.py --image "$request_dir/reference.png" --output "$run/shape" --seed "$seed"
  conda activate /workspace/hunyuan21/texture-environment
  export TMPDIR=/workspace/hunyuan21/tmp/texture
  export PYTHONPATH=/project/arc/scripts:/workspace/hunyuan21/texture-source/hy3dpaint:/workspace/hunyuan21/texture-source/hy3dshape
  export LD_LIBRARY_PATH=/workspace/hunyuan21/texture-environment/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
  cd /workspace/hunyuan21/texture-source
  python -u /project/arc/scripts/paint_hunyuan_asset.py --source "$run/shape" --output "$run/paint"
  python /project/arc/scripts/hunyuan_variant.py package "$request_dir" "$run"
'
cp "$run/result.zip" "$variant_dir/result.zip.tmp"
mv "$variant_dir/result.zip.tmp" "$variant_dir/result.zip"
echo "DOWNLOAD THIS FILE: $variant_dir/result.zip"
echo 'Import it under Asset library in the local frontend. Blender/Chaos preparation has not run.'
