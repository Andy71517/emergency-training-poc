#!/bin/bash

# Submit the one-time, project-storage TRELLIS.2 runtime build. This does not
# download TRELLIS.2 model weights and does not generate an asset.
set -euo pipefail

# shellcheck source=load_arc_config.sh
source "$(dirname "$0")/load_arc_config.sh"

for variable_name in ARC_TRELLIS2_REPOSITORY ARC_TRELLIS2_REVISION ARC_TRELLIS2_CONTAINER_IMAGE; do
  if [[ -z "${!variable_name:-}" ]]; then
    echo "$variable_name is required in arc/.env before building TRELLIS.2." >&2
    exit 2
  fi
done

sbatch --account="$ARC_ACCOUNT" --partition="$ARC_GPU_PARTITION" --qos="$ARC_GPU_QOS" arc/jobs/build_trellis2_runtime.sbatch
