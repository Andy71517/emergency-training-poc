#!/bin/bash

# Submit a short import and CUDA check for a previously built TRELLIS.2 runtime.
set -euo pipefail

# shellcheck source=load_arc_config.sh
source "$(dirname "$0")/load_arc_config.sh"

sbatch --account="$ARC_ACCOUNT" --partition="$ARC_GPU_PARTITION" --qos="$ARC_GPU_QOS" arc/jobs/verify_trellis2_runtime.sbatch
