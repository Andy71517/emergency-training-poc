#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/load_arc_config.sh"
source "$(dirname "$0")/hunyuan_texture_config.sh"
case "${1:-}" in
  build)
    [[ -f "$ARC_HUNYUAN_ROOT/metadata/runtime-ready.env" ]] || { echo "Verify the shape runtime first." >&2; exit 2; }
    job=arc/jobs/build_hunyuan_texture.sbatch ;;
  paint)
    shape_job="${2:-}"
    [[ "$shape_job" =~ ^[0-9]+$ ]] || { echo "Usage: bash $0 paint SHAPE_JOB_ID" >&2; exit 2; }
    [[ -f "$ARC_HUNYUAN_ROOT/metadata/texture-ready.env" ]] || { echo "Build and verify the texture runtime first." >&2; exit 2; }
    for name in chair.glb manifest.json input-foreground.png; do
      [[ -f "$ARC_HUNYUAN_ROOT/outputs/wooden-chair-$shape_job/$name" ]] || { echo "Missing source file: $name" >&2; exit 2; }
    done
    export HUNYUAN_SHAPE_JOB_ID="$shape_job"
    job=arc/jobs/texture_hunyuan_chair.sbatch ;;
  *) echo "Usage: bash $0 build | paint SHAPE_JOB_ID" >&2; exit 2 ;;
esac
bash arc/scripts/check_hunyuan_texture_access.sh
mkdir -p arc/results
sbatch --account="$ARC_ACCOUNT" --partition="$ARC_GPU_PARTITION" --qos="$ARC_GPU_QOS" "$job"
