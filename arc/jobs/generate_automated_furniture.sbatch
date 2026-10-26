#!/bin/bash
#SBATCH --job-name=fieldwork-asset
#SBATCH --time=02:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --gres=gpu:1
#SBATCH --output=arc/results/automated-asset-%j.out
#SBATCH --error=arc/results/automated-asset-%j.err
set -euo pipefail
umask 077
source arc/scripts/load_arc_config.sh
source arc/scripts/hunyuan_texture_config.sh
[[ "${FIELDWORK_DISPATCH:-}" =~ ^[a-f0-9]{32}$ ]] || exit 2
run="$ARC_HUNYUAN_ROOT/automation/$FIELDWORK_DISPATCH"
exec 9>"$run/generation.lock"
flock -n 9 || exit 2
export HUNYUAN_SOURCE_REVISION="$ARC_HUNYUAN_SOURCE_REVISION"
export HUNYUAN_PAINT_REVISION="$ARC_HUNYUAN_PAINT_REVISION"
export HUNYUAN_DINO_REVISION="$ARC_HUNYUAN_DINO_REVISION"
export HUNYUAN_TEXTURE_SOURCE_REVISION="$ARC_HUNYUAN_SOURCE_REVISION"
unset ARC_LLM_API_KEY OPENAI_API_KEY HF_TOKEN
export APPTAINER_CACHEDIR="$ARC_PROJECT_WORKSPACE/cache/apptainer"
export APPTAINER_TMPDIR="$ARC_PROJECT_WORKSPACE/cache/apptainer-tmp"
module load apptainer
apptainer exec --nv --bind "$ARC_PROJECT_WORKSPACE:/workspace" --bind "$PWD:/project" "$ARC_HUNYUAN_CONTAINER" /bin/bash -lc '
  set -euo pipefail
  export HOME=/workspace/hunyuan21/home
  export TMPDIR=/workspace/hunyuan21/tmp
  export HF_HOME=/workspace/hunyuan21/cache/huggingface
  export U2NET_HOME=/workspace/hunyuan21/cache/rembg
  run="/workspace/hunyuan21/automation/$FIELDWORK_DISPATCH"
  source /opt/conda/etc/profile.d/conda.sh
  conda activate /workspace/hunyuan21/environment
  export PYTHONPATH=/workspace/hunyuan21/source/hy3dshape:/project/arc/scripts
  export LD_LIBRARY_PATH=/workspace/hunyuan21/environment/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
  printf image > "$run/phase"
  python -u /project/arc/scripts/generate_furniture_reference.py --prompt "$run/prompt.json" --output "$run/request"
  seed=$(python -c "import json; print(json.load(open(\"$run/prompt.json\"))[\"seed\"])")
  cd /workspace/hunyuan21/source
  printf shape > "$run/phase"
  python -u /project/arc/scripts/generate_hunyuan_asset.py --image "$run/request/reference.png" --output "$run/shape" --seed "$seed"
  conda activate /workspace/hunyuan21/texture-environment
  export TMPDIR=/workspace/hunyuan21/tmp/texture
  export PYTHONPATH=/project/arc/scripts:/workspace/hunyuan21/texture-source/hy3dpaint:/workspace/hunyuan21/texture-source/hy3dshape
  export LD_LIBRARY_PATH=/workspace/hunyuan21/texture-environment/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
  cd /workspace/hunyuan21/texture-source
  printf texture > "$run/phase"
  python -u /project/arc/scripts/paint_hunyuan_asset.py --source "$run/shape" --output "$run/paint"
  python /project/arc/scripts/hunyuan_variant.py package "$run/request" "$run"
  python /project/arc/scripts/remote_asset_control.py package "$FIELDWORK_DISPATCH" --root /workspace/hunyuan21/automation
  printf packaged > "$run/phase"
'
