#!/bin/bash
set -euo pipefail
source "$(dirname "$0")/load_arc_config.sh"

input="$ARC_PROJECT_WORKSPACE/trellis2/inputs/wooden-chair.png"
if [[ ! -f "$input" ]]; then
  echo "Upload the chair reference image to $input before submitting." >&2
  exit 2
fi
sbatch --account="$ARC_ACCOUNT" --partition="$ARC_GPU_PARTITION" --qos="$ARC_GPU_QOS" arc/jobs/generate_trellis2_chair.sbatch
