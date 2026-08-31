#!/bin/bash

# Submit the short GPU-backed Apptainer smoke check using only the ignored local
# ARC configuration file.

set -euo pipefail

# shellcheck source=load_arc_config.sh
source "$(dirname "$0")/load_arc_config.sh"

sbatch \
  --account="$ARC_ACCOUNT" \
  --partition="$ARC_GPU_PARTITION" \
  --qos="$ARC_GPU_QOS" \
  arc/jobs/verify_apptainer_a100.sbatch
