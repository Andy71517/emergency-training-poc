#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/load_arc_config.sh"
source "$(dirname "$0")/hunyuan_config.sh"
case "${1:-}" in
  build) job=arc/jobs/build_hunyuan_runtime.sbatch ;;
  chair)
    [[ -f "$ARC_HUNYUAN_INPUT" ]] || { echo "Missing image: $ARC_HUNYUAN_INPUT" >&2; exit 2; }
    [[ -f "$ARC_HUNYUAN_ROOT/metadata/runtime-ready.env" ]] || { echo "Run and verify the Hunyuan build first." >&2; exit 2; }
    job=arc/jobs/generate_hunyuan_chair.sbatch ;;
  *) echo "Usage: bash arc/scripts/submit_hunyuan.sh build|chair" >&2; exit 2 ;;
esac
[[ -f "$ARC_HUNYUAN_CONTAINER" ]] || { echo "Missing existing container: $ARC_HUNYUAN_CONTAINER" >&2; exit 2; }
bash arc/scripts/check_hunyuan_access.sh
mkdir -p arc/results
sbatch --account="$ARC_ACCOUNT" --partition="$ARC_GPU_PARTITION" --qos="$ARC_GPU_QOS" "$job"
